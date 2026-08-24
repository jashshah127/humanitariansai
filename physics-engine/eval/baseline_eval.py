"""
Baseline harness: measures how often PLAIN LLM chain-of-thought (no tool use, no
SymPy, the model just reasoning it out and doing its own arithmetic) gets these
problems right. This is the number Phase 0 asks for and the number the whole
engine exists to beat -- run this BEFORE getting excited about the engine's own
accuracy, or there's nothing to compare it to.

Needs API keys (only wherever you run this -- not inside the build sandbox, no
network there):
    export ANTHROPIC_API_KEY=...
    export OPENAI_API_KEY=...      # optional, only if you also want a GPT data point

Setup:
    pip install anthropic openai pandas

Run against our own 16-problem starter set (already has verified answers):
    python baseline_eval.py --input golden_set_16.csv --model claude

Run against a pulled UGPhysics subset once pull_ugphysics_subset.py has been run
elsewhere and the CSV handed over (note: UGPhysics's own answer format needs a
column rename first -- see `--ugphysics` flag below):
    python baseline_eval.py --input ugphysics_ClassicalMechanics.csv --model claude --ugphysics
"""
import argparse
import json
import re
import sys

import pandas as pd

PROMPT_TEMPLATE = """Solve this physics problem. Show your work, then give your final answer(s)
on their own line(s), one per requested quantity, in exactly this form:
FINAL ANSWER: <quantity name> = <value> <units>

If there is only one quantity asked for, still use a quantity name (e.g. "v" or "F").

Problem: {problem}
"""


def call_gemini(problem_text, model="gemini-flash-lite-latest"):
    """FREE option -- no credit card. Get a key at aistudio.google.com/apikey, then
    export GEMINI_API_KEY. Paced under the free-tier rate limit."""
    import json as _json
    import os
    import time
    import urllib.request

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set. Free key at aistudio.google.com/apikey")

    global _LAST_GEMINI_CALL
    wait = 6.5 - (time.time() - _LAST_GEMINI_CALL)
    if wait > 0:
        time.sleep(wait)
    _LAST_GEMINI_CALL = time.time()

    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent")
    body = _json.dumps({
        "contents": [{"parts": [{"text": PROMPT_TEMPLATE.format(problem=problem_text)}]}],
        "generationConfig": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "X-goog-api-key": key,
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return _json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


_LAST_GEMINI_CALL = 0.0


def call_claude(problem_text, model="claude-sonnet-4-6"):
    import anthropic
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(problem=problem_text)}],
    )
    return resp.content[0].text


def call_gpt(problem_text, model="gpt-4o"):
    import openai
    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(problem=problem_text)}],
    )
    return resp.choices[0].message.content


def extract_answers(response_text):
    """Returns {quantity_name: float}. Handles the multi-quantity case
    (e.g. a projectile problem asking for t_flight, h_max, AND range)."""
    out = {}
    for m in re.finditer(r"FINAL ANSWER:\s*([\w_]+)\s*=\s*([-\d.eE+]+)", response_text):
        try:
            out[m.group(1)] = float(m.group(2))
        except ValueError:
            continue
    return out


def values_match(got, expected, rel_tol=1e-2):
    if got is None:
        return False
    if expected == 0:
        return abs(got) < 1e-6
    return abs(got - expected) / abs(expected) < rel_tol


def score_one(raw_response, expected_dict):
    """expected_dict: {quantity_name: value}. Returns (all_correct, per_quantity_detail)."""
    got_dict = extract_answers(raw_response)
    detail = {}
    all_correct = True
    for name, expected_val in expected_dict.items():
        got_val = got_dict.get(name)
        ok = values_match(got_val, expected_val)
        detail[name] = {"got": got_val, "expected": expected_val, "correct": ok}
        all_correct = all_correct and ok
    return all_correct, detail


def run_baseline(df, model_fn, expected_col="expected_json"):
    """df needs columns: problem_id, problem_text, expected_json (a JSON string
    like '{"v": 30.0, "s": 180.0}')."""
    results = []
    n = len(df)
    for i, row in df.iterrows():
        print(f"  [{i+1}/{n}] {row['problem_id']}...", file=sys.stderr)
        raw = model_fn(row["problem_text"])
        expected = json.loads(row[expected_col])
        all_correct, detail = score_one(raw, expected)
        results.append({
            "problem_id": row["problem_id"],
            "all_correct": all_correct,
            "detail": detail,
            "raw_response": raw,
        })
    acc = sum(r["all_correct"] for r in results) / len(results) if results else 0.0
    return acc, results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True,
                         help="CSV with columns: problem_id, problem_text, expected_json")
    parser.add_argument("--model", choices=["gemini", "claude", "gpt"], default="gemini",
                         help="gemini = FREE tier, no credit card (default)")
    parser.add_argument("--ugphysics", action="store_true",
                         help="Input is a raw UGPhysics export -- remap columns first "
                              "(problem->problem_text, index->problem_id). NOTE: UGPhysics's "
                              "'answers' column is a boxed-LaTeX string, not JSON -- you'll need "
                              "to hand-check or write a small parser for it before this flag is "
                              "fully automatic. Flagged here rather than faked.")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    if args.ugphysics:
        df = df.rename(columns={"problem": "problem_text", "index": "problem_id"})
        print("NOTE: --ugphysics remaps text columns but does NOT auto-convert the "
              "'answers' field (boxed LaTeX) into expected_json. Do that conversion "
              "before running, or this will error on json.loads().", file=sys.stderr)

    model_fn = {"gemini": call_gemini, "claude": call_claude, "gpt": call_gpt}[args.model]
    acc, results = run_baseline(df, model_fn)

    print(f"\nBaseline accuracy ({args.model}, NO tool use, plain chain-of-thought): {acc:.1%}")
    out_path = f"baseline_results_{args.model}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Full results, including every wrong answer for error analysis -> {out_path}")
    print("Compare this number directly against the engine's 16/16 (100%) on the same")
    print("problems -- that gap IS the silent-computation-error failure mode this project exists to close.")
