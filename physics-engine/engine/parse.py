"""
PARSE -- the Phase 1 stage. Turns raw problem text into the structured
knowns/unknowns the Phase 0 solver already expects.

This is the piece the brief always assigned to the LLM ("the LLM handles problem
understanding, formula selection, and explanation") and that the Phase 0 prototype
deliberately stubbed out. It is the only stage where a language model does anything,
and it is confined to reading comprehension: extract numbers and name the target
quantity. It never computes, never rearranges a formula, never picks a value.

DESIGN NOTE -- why the LLM call is injected rather than hardcoded:
  * the engine stays testable with no network and no API key (see StubLLM below,
    which is what lets the Phase 1 demo run end-to-end in CI);
  * the API key never has to live inside the engine package;
  * swapping Claude for another model, or for a fine-tuned model in the tier-3
    roadmap, is a constructor argument rather than an edit to the solver.

TRACEABILITY: the brief requires parsed values be "traceable back to the source
text." Every known therefore carries the phrase it came from, so a wrong answer can
be traced to a misread number rather than blamed vaguely on "the parser."
"""
import json
import sympy as sp
import re

from formula_kb import ALL_CARDS
from variable_glossary import (
    glossary_for_prompt,
    normalize_parse,
    normalize_name,
    inject_constants,
    GLOSSARY,
)

PARSE_PROMPT = """You are the parsing stage of a physics problem-solving engine. Your ONLY job is
reading comprehension: pull the stated quantities out of the problem and name what is being
asked for. You must NOT solve anything, rearrange any formula, or compute any value.

Use EXACTLY these variable names. Do not invent new ones:

{glossary}

Rules:
- Convert every value to SI base units before reporting it (25 km -> 25000, 100 uF -> 0.0001,
  2 kOhm -> 2000). Report the converted number, not the original.
- EXCEPTION: `theta_deg` stays in degrees. Never convert it to radians.
- IF A QUANTITY IS GIVEN AS A SYMBOL RATHER THAN A NUMBER -- "a particle of mass m",
  "a charge q", "radius R" -- report it as {{"symbolic": true}} instead of a value.
  DO NOT invent a number like 1.0 for it. The engine can solve symbolically and will
  return a formula; inventing a value produces a confidently wrong number instead.
- Charges go in as MAGNITUDES (q1_abs, q2_abs are always positive). Sign only sets direction,
  which is not your job.
- Do NOT include physical constants (g, G, k_e, epsilon_0, mu_0). Those are supplied
  automatically. Only report what the problem itself states.
- "starts from rest" / "initially at rest" means v0 = 0. State it explicitly.
- For every known, include the exact phrase from the problem it came from.
- If a quantity you would need is genuinely not stated at all, leave it out. Do not guess it.

Respond with ONLY a JSON object, no prose and no markdown fences:

{{
  "topic_hint": "Mechanics" or "E&M" or "Thermodynamics",
  "knowns": {{"<name>": {{"value": <number>, "source": "<exact phrase>"}},
              "<name>": {{"symbolic": true, "source": "<exact phrase>"}}}},
  "unknowns": ["<name>", ...],
  "notes": "<anything ambiguous, or empty string>"
}}

Problem:
{problem}
"""


class ParseError(Exception):
    """Raised when the LLM's output cannot be read as a parse at all.
    Deliberately distinct from 'parsed fine but nothing in the KB covers it' --
    those are different failures needing different fixes."""


# ---------------------------------------------------------------------------
# LLM callers
# ---------------------------------------------------------------------------
class ClaudeLLM:
    """Production caller. Needs ANTHROPIC_API_KEY in the environment.

    temperature=0 is deliberate, not cosmetic: parse is the one stage where model
    sampling could make the same problem produce different outputs, which is the exact
    instability the V2 routing work exists to eliminate. The solver downstream cannot
    vary; this makes the stage above it vary as little as the API allows."""

    def __init__(self, model="claude-sonnet-4-6"):
        self.model = model

    def __call__(self, prompt):
        import anthropic
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text


class GeminiLLM:
    """FREE option. Google AI Studio's free tier needs no credit card and does not
    expire: roughly 1,500 requests/day at 15 RPM on Flash models, which is ample for a
    benchmark run of a few hundred problems.

    Get a key at aistudio.google.com -> Get API key. Then:
        export GEMINI_API_KEY=...

    Uses raw REST through the standard library, deliberately: no SDK to install, and
    no exposure to SDK version drift on someone else's machine.

    Built-in pacing. The free tier allows ~15 requests/minute, so this sleeps between
    calls rather than letting a 200-problem run die on 429s halfway through.

    ONE THING TO KNOW, given this project's own data-governance thread: Google may use
    free-tier prompts to improve their products. That is fine for UGPhysics problems,
    which are public benchmark data. It is NOT fine for student work -- do not point
    this provider at anything student-linked. Use a paid tier or a local model for that.
    """

    def __init__(self, model="gemini-flash-latest", min_interval=6.5):
        self.model = model
        self.min_interval = min_interval   # ~9 req/min, under the 10 RPM free-tier floor
        self._last = 0.0

    def __call__(self, prompt):
        import json as _json
        import os
        import time
        import urllib.request

        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ParseError("GEMINI_API_KEY not set. Get a free key at aistudio.google.com/apikey")

        wait = self.min_interval - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.time()

        # Auth goes in the X-goog-api-key HEADER, not a ?key= query parameter. Newer
        # AI Studio keys (the AQ.* format) are auth keys and the header is what Google's
        # own current examples use; the query-param form is the older style and can be
        # rejected outright.
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent")
        body = _json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0},
        }).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "X-goog-api-key": key,
        })
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = _json.loads(r.read())
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                detail = ""
                if hasattr(e, "read"):
                    try:
                        detail = e.read().decode()[:300]
                    except Exception:
                        pass
                if attempt == 3:
                    raise ParseError(f"Gemini call failed after retries: {e} {detail}")
                time.sleep(2 ** attempt)   # backoff on 429 / transient errors


class OllamaLLM:
    """FREE and fully local -- no key, no network, no data leaving the machine.

        brew install ollama && ollama serve
        ollama pull llama3.2

    Slower than a hosted model, and a small local model will parse less reliably than
    Gemini Flash. But parse is structured extraction rather than hard reasoning, so it
    is worth trying before assuming it is inadequate -- and unlike the hosted options
    it is the only one safe to point at student work, since nothing leaves the machine.
    """

    def __init__(self, model="llama3.2", host="http://localhost:11434"):
        self.model = model
        self.host = host

    def __call__(self, prompt):
        import json as _json
        import urllib.request

        body = _json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        }).encode()
        req = urllib.request.Request(f"{self.host}/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return _json.loads(r.read())["response"]
        except Exception as e:
            raise ParseError(f"Ollama call failed (is `ollama serve` running?): {e}")


class StubLLM:
    """Offline caller for tests and CI. Looks up a canned parse by matching
    distinctive phrases in the problem text.

    This is a TEST DOUBLE, not a parser. It proves the plumbing around parse works
    (normalization, constant injection, error handling, event logging, routing);
    it proves nothing about whether a real model parses well. That measurement needs
    the API and is called out as still-open in the Phase 1 README."""

    def __init__(self, canned):
        self.canned = canned
        self.calls = []

    def __call__(self, prompt):
        self.calls.append(prompt)
        # Match against the PROBLEM only, never the whole prompt. The prompt embeds the
        # glossary, whose descriptions contain physics phrases ("coefficient of kinetic
        # friction") that will match a trigger meant for a different problem and hand back
        # the wrong canned parse -- which then solves cleanly and returns a confidently
        # WRONG verified answer. Found exactly that way; the fix is to scope the match.
        problem = prompt.split("Problem:", 1)[-1].strip().lower()
        for trigger, response in self.canned.items():
            if trigger.lower() in problem:
                return json.dumps(response)
        raise ParseError("StubLLM has no canned parse matching this problem")


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------
def _extract_json(text):
    """Pull a JSON object out of a model response, tolerating markdown fences or
    a stray sentence of preamble."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ParseError(f"no JSON object found in model response: {text[:200]}")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise ParseError(f"malformed JSON in model response: {e}")


def parse_problem(raw_problem, llm):
    """raw_problem: str. llm: callable(prompt) -> str.

    Returns a parse dict:
        knowns      {name: float}          -- ready for the solver
        unknowns    [name, ...]
        topic_hint  "Mechanics" | "E&M" | None
        sources     {name: source phrase}  -- traceability
        injected    {name: value}          -- constants added, not parsed
        normalization {renamed, unrecognized}
        raw         the model's own JSON, kept for debugging
    """
    prompt = PARSE_PROMPT.format(glossary=glossary_for_prompt(), problem=raw_problem)
    payload = _extract_json(llm(prompt))

    raw_knowns = payload.get("knowns", {})
    raw_unknowns = payload.get("unknowns", [])
    if not isinstance(raw_knowns, dict) or not isinstance(raw_unknowns, list):
        raise ParseError("model returned knowns/unknowns in an unexpected shape")

    # Accept the rich {"value":..,"source":..} form, the {"symbolic": true} form, and a
    # bare number, so a slightly-off model response degrades to a working parse rather
    # than failing outright.
    values, sources, symbolic_names = {}, {}, []
    for name, entry in raw_knowns.items():
        if isinstance(entry, dict):
            if entry.get("symbolic") is True or entry.get("value") in ("symbolic", None):
                values[name] = sp.Symbol(name)
                symbolic_names.append(name)
            else:
                values[name] = entry.get("value")
            sources[name] = entry.get("source", "")
        else:
            values[name] = entry
            sources[name] = ""

    bad = [n for n, v in values.items()
           if not isinstance(v, (int, float)) and not isinstance(v, sp.Basic)]
    if bad:
        raise ParseError(f"non-numeric, non-symbolic values for: {bad}")

    knowns, unknowns, norm_report = normalize_parse(values, raw_unknowns)
    sources = {normalize_name(k)[0]: v for k, v in sources.items()}

    # Symbols must carry the CANONICAL name, not whatever the model called it. Creating
    # them before normalization produced answers like 9.8*(-mass_1 + mass_2)/(mass_1 +
    # mass_2) -- correct algebra wearing the parser's vocabulary instead of the physics
    # vocabulary, which is useless to a student and unmatchable against a benchmark.
    symbolic_names = [normalize_name(n)[0] for n in symbolic_names]
    for canonical in symbolic_names:
        if canonical in knowns:
            knowns[canonical] = sp.Symbol(canonical)

    knowns, injected = inject_constants(knowns, unknowns, ALL_CARDS)

    return {
        "knowns": knowns,
        "unknowns": unknowns,
        "topic_hint": payload.get("topic_hint"),
        "sources": sources,
        "injected": injected,
        "symbolic_knowns": symbolic_names,
        "normalization": norm_report,
        "notes": payload.get("notes", ""),
        "raw": payload,
    }
