"""
CLASSIFIER -- tags a problem with topic, subtopic, grade level and difficulty, for the
de-identified problems_log and the admin dashboard.

Design (see the classification pipeline plan):

  1. THE ENGINE FIRST. If the engine solved the problem through exactly one formula card
     (route "deterministic_script"), that card's topic/subtopic is a trusted label -- the
     card IS the physics that was applied. The model is then only needed for grade and
     difficulty, and a model that disagrees on topic is flagged for review, not believed.
  2. SCHEMA-ENFORCED OUTPUT. The model answers through a response schema whose topic,
     subtopic, grade and difficulty fields are enums, so the reply always parses and every
     value is from the allowed lists. (Tested: "reply in JSON" prompting failed 0/3 on
     format; schema-enforced output passed 3/3.) The model can still pick a wrong value --
     a schema guarantees shape, not correctness -- so the (topic, subtopic) PAIR is checked
     too, against the same pairs the database's `topics` table allows.
  3. NEVER BREAK /solve. Tagging runs after the student has their answer. Every failure
     becomes either a partial result (card topic, no grade/difficulty) or ClassifyError,
     and the caller then logs the problem untagged.

Self-reported confidence is kept, but only for ordering a review queue -- it was flat
(0.95-1.00) in testing, so it is not treated as a probability.

The model call is injected (`llm`), as in parse.py, so tests run offline with no key.
Standard library only.
"""
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from typing import Optional

from formula_kb import ALL_CARDS

# ---------------------------------------------------------------- label set

OTHER = ("Other", "Other")
# The allowed (topic, subtopic) pairs: every formula card's labels, plus Other/Other.
# Must match the rows seeded into public.topics (checked in ci_check.py).
TOPIC_PAIRS = sorted({(c.topic, c.subtopic) for c in ALL_CARDS}) + [OTHER]
TOPICS = sorted({t for t, _ in TOPIC_PAIRS})
SUBTOPICS = sorted({s for _, s in TOPIC_PAIRS})
GRADES = ["high_school", "intro_undergrad", "upper_undergrad", "graduate"]
DIFFICULTIES = ["easy", "medium", "hard"]
_CARDS_BY_ID = {c.id: c for c in ALL_CARDS}

SCHEMA = {
    "type": "OBJECT",
    "required": ["topic", "subtopic", "grade_level", "difficulty", "confidence"],
    "properties": {
        "topic": {"type": "STRING", "enum": TOPICS},
        "subtopic": {"type": "STRING", "enum": SUBTOPICS},
        "grade_level": {"type": "STRING", "enum": GRADES},
        "difficulty": {"type": "STRING", "enum": DIFFICULTIES},
        "confidence": {"type": "NUMBER"},
    },
}

PROMPT = """Classify this physics problem. Do not solve it.

topic and subtopic: choose the pair that fits best from:
{pairs}
Use Other / Other if none of them fits.

grade_level:
  high_school      algebra-based; a single formula; no calculus
  intro_undergrad  first-year calculus-based physics
  upper_undergrad  multi-step derivations, differential equations, vector calculus
  graduate         beyond the undergraduate curriculum

difficulty:
  easy    one formula, values given directly
  medium  two or more steps, or one quantity must be derived first
  hard    several principles combined, or a symbolic / derivation answer

confidence: a number from 0 to 1.

Problem:
{problem}
"""


class ClassifyError(Exception):
    """No tags could be produced at all. The caller logs the problem untagged."""


@dataclass
class Classification:
    topic: Optional[str]
    subtopic: Optional[str]
    grade_level: Optional[str]
    difficulty: Optional[str]
    confidence: Optional[float]
    source: str                   # "engine_card" (topic from the matched card) or "llm"
    model: Optional[str]          # which model produced grade/difficulty (None if none did)
    needs_review: bool
    review_reason: Optional[str]

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------- the model call

class GeminiClassifierLLM:
    """Gemini with a response schema, pinned models and failure handling.

    Callable as llm(prompt, schema) -> (reply_text, model_name).
      503 / timeout / connection error -> retry with backoff, then the next model
      429 (quota used)                 -> next model at once; retrying burns more quota
      404 (model retired)              -> next model at once
      any other error                  -> stop: the request itself is wrong
    """

    def __init__(self, models=("gemini-3.8-flash", "gemini-3.6-flash"), waits=(2, 5),
                 timeout=30, post=None, sleep=time.sleep):
        self.models, self.waits, self.timeout = list(models), waits, timeout
        self._post, self._sleep = post or self._urllib_post, sleep

    @staticmethod
    def _urllib_post(url, body, headers, timeout):
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def __call__(self, prompt, schema):
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ClassifyError("GEMINI_API_KEY not set")
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                           "generationConfig": {"temperature": 0,
                                                "responseMimeType": "application/json",
                                                "responseSchema": schema}}).encode()
        headers = {"Content-Type": "application/json", "X-goog-api-key": key}
        errors = []
        for model in self.models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            for attempt in range(len(self.waits) + 1):
                try:
                    status, raw = self._post(url, body, headers, self.timeout)
                except (TimeoutError, urllib.error.URLError, ConnectionError, OSError) as e:
                    status, raw = None, type(e).__name__.encode()
                if status == 200:
                    try:
                        return json.loads(raw)["candidates"][0]["content"]["parts"][0]["text"], model
                    except (ValueError, KeyError, IndexError, TypeError):
                        errors.append(f"{model}: unreadable reply")
                        break
                if status in (404, 429):
                    errors.append(f"{model}: {status}")
                    break
                if status is not None and status != 503:
                    raise ClassifyError(f"{model}: HTTP {status} (not retryable)")
                if attempt < len(self.waits):
                    self._sleep(self.waits[attempt])
            else:
                errors.append(f"{model}: unavailable after retries")
        raise ClassifyError("all models failed: " + "; ".join(errors))


# ---------------------------------------------------------------- classify

def _card_pair(solution):
    """(topic, subtopic) of the single matched card, or None."""
    if not solution or solution.get("route") != "deterministic_script":
        return None
    card = _CARDS_BY_ID.get((solution.get("retrieve") or {}).get("matched"))
    return (card.topic, card.subtopic) if card else None


def classify(problem_text, solution=None, llm=None):
    """Tag one problem. `problem_text` must already be cleaned of personal details.
    `solution` is the engine's solution object for this problem, if there is one.
    `llm` is callable(prompt, schema) -> (reply_text, model); defaults to Gemini.

    Returns a Classification, or raises ClassifyError when nothing could be tagged."""
    card = _card_pair(solution)
    pairs = "\n".join(f"  {t} / {s}" for t, s in TOPIC_PAIRS)
    llm = llm or GeminiClassifierLLM()

    try:
        reply, model = llm(PROMPT.format(pairs=pairs, problem=problem_text), SCHEMA)
        tags = json.loads(reply)
        if not isinstance(tags, dict):
            raise ValueError("reply is not an object")
    except (ClassifyError, ValueError, TypeError) as e:
        if card:  # the model failed, but the engine already knows the topic
            return Classification(card[0], card[1], None, None, None, "engine_card", None,
                                  False, None)
        raise ClassifyError(f"no tags: {e}")

    grade = tags.get("grade_level") if tags.get("grade_level") in GRADES else None
    difficulty = tags.get("difficulty") if tags.get("difficulty") in DIFFICULTIES else None
    try:
        confidence = float(tags.get("confidence"))
    except (TypeError, ValueError):
        confidence = None
    llm_pair = (tags.get("topic"), tags.get("subtopic"))

    if card:
        agrees = llm_pair == card
        return Classification(card[0], card[1], grade, difficulty, confidence, "engine_card", model,
                              not agrees, None if agrees else f"model said {llm_pair[0]} / {llm_pair[1]}")

    if llm_pair not in TOPIC_PAIRS:   # each field valid on its own, but not a real pair
        return Classification(OTHER[0], OTHER[1], grade, difficulty, confidence, "llm", model,
                              True, f"invalid pair {llm_pair[0]} / {llm_pair[1]}")
    if llm_pair == OTHER:
        return Classification(OTHER[0], OTHER[1], grade, difficulty, confidence, "llm", model,
                              True, "outside the formula library")
    return Classification(llm_pair[0], llm_pair[1], grade, difficulty, confidence, "llm", model,
                          False, None)
