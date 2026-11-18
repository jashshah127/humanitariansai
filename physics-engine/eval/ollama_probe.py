"""Run ONE golden-set problem through Ollama parse -> engine. Shows raw model output,
time per call, and whether the final answer matches. Takes seconds, not 20 minutes.

Usage (from physics-engine/):
    python eval\\ollama_probe.py --csv eval\\golden_set_16.csv --row 0
    python eval\\ollama_probe.py --csv eval\\golden_set_16.csv --row 0 --model qwen2.5:7b
"""
import argparse
import csv
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))

from parse import OllamaLLM, PARSE_PROMPT, glossary_for_prompt, _extract_json, parse_problem, ParseError  # noqa: E402
from pipeline import solve_physics_problem  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--csv", required=True)
ap.add_argument("--row", type=int, default=0)
ap.add_argument("--model", default="llama3.2")
a = ap.parse_args()

row = list(csv.DictReader(open(a.csv, encoding="utf-8")))[a.row]
text, expected = row["problem_text"], json.loads(row["expected_json"])
print(f"PROBLEM {row['problem_id']}: {text}\nEXPECTED: {expected}\nMODEL: {a.model}\n")

llm = OllamaLLM(model=a.model)
t0 = time.time()
raw = llm(PARSE_PROMPT.format(glossary=glossary_for_prompt(), problem=text))
print(f"--- RAW MODEL OUTPUT ({time.time() - t0:.1f}s) ---\n{raw}\n")

try:
    _extract_json(raw)
    print("JSON: valid")
except ParseError as e:
    sys.exit(f"JSON: INVALID -> {e}")

t0 = time.time()
try:
    parsed = parse_problem(text, llm)   # second call, so this also shows run-to-run stability
except ParseError as e:
    sys.exit(f"parse_problem failed: {e}")
print(f"PARSED ({time.time() - t0:.1f}s): knowns={parsed['knowns']} unknowns={parsed['unknowns']} "
      f"topic={parsed.get('topic_hint')}\nnormalization={parsed.get('normalization')}")

sol = solve_physics_problem(row["problem_id"], text, parsed["knowns"], parsed["unknowns"],
                            topic_hint=parsed.get("topic_hint"))
print(f"\nROUTE: {sol['route']}\nENGINE ANSWER: {sol.get('final_answer')}\nEXPECTED:      {expected}")