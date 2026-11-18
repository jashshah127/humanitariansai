"""
Read benchmark_results.json and show WHY each attempted problem failed, compactly.

Usage (from the physics-engine folder):
    python eval\\inspect_results.py
    python eval\\inspect_results.py --file my_run.json
"""
import argparse
import json
from collections import Counter

ap = argparse.ArgumentParser()
ap.add_argument("--file", default="benchmark_results.json")
args = ap.parse_args()

with open(args.file, encoding="utf-8") as f:
    data = json.load(f)
rows = data["rows"]
print(f"run: {data['summary']['meta']}\n")

name_counter = Counter()

print("=" * 70)
print("DECLINED -- what the model asked for, and which names the glossary didn't know")
print("=" * 70)
for r in rows:
    if r["outcome"] not in ("declined_no_card", "declined_missing_knowns"):
        continue
    p = r.get("parse") or {}
    unknown_names = p.get("unrecognized_names") or []
    name_counter.update(unknown_names)
    parsed_knowns = [k for k in (p.get("knowns") or {}) if k not in (p.get("injected_constants") or {})]
    print(f"\n{r['problem_id']}  [{r['outcome']}]")
    print(f"  unknowns     : {p.get('unknowns')}")
    print(f"  knowns       : {parsed_knowns}")
    print(f"  unrecognized : {unknown_names}")
    if p.get("renamed"):
        print(f"  renamed      : {p.get('renamed')}")
    if p.get("formula_given_as_value"):
        print(f"  formula as value (model wrote a relation into knowns): {p.get('formula_given_as_value')}")
    if r["outcome"] == "declined_missing_knowns":
        for a in r.get("plan_attempts") or []:
            print(f"  card {a.get('card_id')}: {a.get('reason')}")

print("\n" + "=" * 70)
print("PARSE FAILED -- error, then the start of the model's reply")
print("=" * 70)
for r in rows:
    if r["outcome"] not in ("parse_failed_bad_output", "parse_found_no_unknown"):
        continue
    print(f"\n{r['problem_id']}  [{r['outcome']}]")
    if r.get("detail"):
        print(f"  error : {r['detail']}")
    raw = (r.get("raw_reply") or "").replace("\n", " ")
    print(f"  reply : {raw[:300]}")

print("\n" + "=" * 70)
print("MOST COMMON UNRECOGNIZED NAMES (across all declines)")
print("=" * 70)
for name, n in name_counter.most_common(25):
    print(f"  {n:3}  {name}")