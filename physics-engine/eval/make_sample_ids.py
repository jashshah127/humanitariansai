"""
Builds the problem-ID lists for the parse-accuracy evaluation. IDs only: no problem
text is written, so the lists are safe to commit (UGPhysics is non-commercial licensed).

Run from physics-engine/:
    python eval/make_sample_ids.py

Writes to eval/sample/:
    ids_pilot.txt        100 problems, stratified by topic and by numeric vs symbolic
    ids_full_01.txt ...  every problem the runner would send to the parser, in batches
                         of 250, numeric-scorable problems first
    sample_summary.txt   the same tables that are printed

Rules (see docs/sampling-plan.md):
  * "Attemptable" = not skipped by the runner (it skips answers with no readable number,
    and true/false or multiple-choice answers).
  * Seed is fixed, so the same CSVs always give the same lists.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pandas as pd  # noqa: E402

import run_benchmark as rb  # noqa: E402

SEED = 2026
BATCH_SIZE = 250
OUT_OF_SCOPE = getattr(rb, "OUT_OF_SCOPE_TYPES", {"TF", "MC"})
SUBJECTS = ["ClassicalMechanics", "ClassicalElectromagnetism"]

# Pilot size per topic (total 100). Roughly proportional to each topic's attemptable
# count, with a floor so every topic is represented.
PILOT_ALLOCATION = {
    "Particle Dynamics": 25,
    "Vibrations and Waves": 15,
    "Electrostatics": 14,
    "Rigid-Body Dynamics": 14,
    "Magstatics": 14,
    "Fluid Mechanics": 7,
    "Central Force Motion": 6,
    "Circuit Analysis": 5,
}

NUMERIC = {"scorable", "partially_numeric"}


def load_attemptable():
    rows = []
    for subject in SUBJECTS:
        df = rb.load(subject)
        for _, r in df.iterrows():
            kind, _ = rb.classify_scorability(r)
            types = {t.strip().split()[0] for t in str(r["answer_type"]).split(",") if t.strip()}
            if kind == "no_number_readable":
                continue
            if types and types <= OUT_OF_SCOPE:
                continue
            rows.append({
                "id": f"{subject}-{r['index']}",
                "subject": subject,
                "topic": r["topic"],
                "class": kind,
                "stratum": "numeric" if kind in NUMERIC else "symbolic",
            })
    return pd.DataFrame(rows)


def split_between(n, a, b):
    """Split n between two groups of size a and b in proportion, at least 1 each when
    both exist, never more than the group has."""
    if a + b == 0:
        return 0, 0
    if a == 0:
        return 0, min(n, b)
    if b == 0:
        return min(n, a), 0
    x = round(n * a / (a + b))
    x = max(1, min(x, n - 1, a))
    y = min(n - x, b)
    x = min(n - y, a)
    return x, y


def build_pilot(d, rng):
    chosen = []
    for topic, n in PILOT_ALLOCATION.items():
        sub = d[d["topic"] == topic]
        if sub.empty:
            raise SystemExit(f"topic not found in the data: {topic}")
        num_ids = sorted(sub[sub["stratum"] == "numeric"]["id"])
        sym_ids = sorted(sub[sub["stratum"] == "symbolic"]["id"])
        n = min(n, len(num_ids) + len(sym_ids))
        k_num, k_sym = split_between(n, len(num_ids), len(sym_ids))
        chosen += rng.sample(num_ids, k_num) + rng.sample(sym_ids, k_sym)
    return sorted(set(chosen))


def build_batches(d):
    order = d.assign(rank=(d["stratum"] != "numeric").astype(int))
    order = order.sort_values(["rank", "subject", "topic", "id"], kind="stable")
    ids = list(order["id"])
    return [ids[i:i + BATCH_SIZE] for i in range(0, len(ids), BATCH_SIZE)]


def main():
    d = load_attemptable()
    rng = random.Random(SEED)
    pilot = build_pilot(d, rng)
    batches = build_batches(d)

    outdir = os.path.join(HERE, "sample")
    os.makedirs(outdir, exist_ok=True)

    def write(name, ids):
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as f:
            f.write("\n".join(ids) + "\n")

    write("ids_pilot.txt", pilot)
    for i, b in enumerate(batches, 1):
        write(f"ids_full_{i:02d}.txt", b)

    lines = [f"Seed {SEED}. Attemptable problems: {len(d)}.", ""]
    lines.append("Attemptable by topic and stratum:")
    lines.append(pd.crosstab(d["topic"], d["stratum"], margins=True).to_string())
    p = d[d["id"].isin(pilot)]
    lines += ["", f"Pilot: {len(pilot)} problems", pd.crosstab(p["topic"], p["stratum"], margins=True).to_string()]
    lines += ["", "Full run batches:"]
    by_id = d.set_index("id")
    for i, b in enumerate(batches, 1):
        n_num = int((by_id.loc[b]["stratum"] == "numeric").sum())
        lines.append(f"  ids_full_{i:02d}.txt: {len(b)} problems ({n_num} numeric, {len(b) - n_num} symbolic)")
    text = "\n".join(lines)
    print(text)
    with open(os.path.join(outdir, "sample_summary.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(f"\nWrote files to {outdir}")


if __name__ == "__main__":
    main()
