"""Summarize benchmark_qwen7b_em40.json: WHY problems failed, not just the % score.
Usage:  python eval\\diag_results.py [path\\to\\benchmark_qwen7b_em40.json]
"""
import json
import sys
from collections import Counter

path = sys.argv[1] if len(sys.argv) > 1 else "benchmark_qwen7b_em40.json"
d = json.load(open(path))
print("SUMMARY:", json.dumps(d["summary"], indent=2))

rows = d["rows"]
print(f"\nRows logged: {len(rows)}  (problems with no readable ground truth are not logged)")
print("\nVerdict counts:")
for v, n in Counter(str(r["verdict"]) for r in rows).most_common():
    print(f"  {n:4}  {v}")

print("\nTop failure reasons:")
for det, n in Counter(str(r.get("detail", ""))[:90] for r in rows).most_common(10):
    print(f"  {n:4}  {det}")

compared = [r for r in rows if "engine" in r]
print(f"\nProblems that actually reached answer comparison: {len(compared)}")
for r in compared[:10]:
    print(f"  {r['problem_id']} [{r['verdict']}]")
    print(f"     engine : {r.get('engine')}  | symbolic: {r.get('engine_symbolic')}")
    print(f"     truth  : {r.get('truth')[:120]}")
    print(f"     detail : {str(r.get('detail'))[:120]}")