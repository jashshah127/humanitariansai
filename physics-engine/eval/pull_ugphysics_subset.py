"""
Run this WHEREVER YOU HAVE INTERNET ACCESS — Colab, your laptop, anywhere with `pip`.
It will not run inside the sandbox this project has been built in (no outbound network there).

What it does: pulls the two UGPhysics subsets that actually match our scope (undergrad
Classical Mechanics + Classical Electromagnetism, not the harder/unrelated subsets),
and writes them to CSV. Hand the two CSVs back and the full crosscheck runs immediately.

Setup (one time):
    pip install datasets pandas

Run:
    python pull_ugphysics_subset.py
"""
from datasets import load_dataset
import pandas as pd

SUBJECTS = ["ClassicalMechanics", "ClassicalElectromagnetism"]

for subject in SUBJECTS:
    print(f"Pulling {subject} ...")
    ds = load_dataset("UGPhysics/ugphysics", subject, split="en")
    df = ds.to_pandas()
    out_path = f"ugphysics_{subject}.csv"
    df.to_csv(out_path, index=False)
    print(f"  -> {len(df)} rows written to {out_path}")
    print(f"  columns: {list(df.columns)}")
    print(f"  sample problem: {df.iloc[0]['problem'][:150]}...")
    print()

print("Done. Send both CSVs back — columns are: index, domain, subject, topic, problem,")
print("solution, answers, answer_type, unit, is_multiple_answer, language, level")
print("(same schema already confirmed against the AtomicPhysics preview.)")
