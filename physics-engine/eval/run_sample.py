"""
Runs the benchmark on a fixed list of problem IDs (see make_sample_ids.py) instead of
the first N rows. It reuses run_benchmark.full_run unchanged, so the outcomes, the
summary and the saved JSON have the same format as a normal run.

Run from physics-engine/:
    python eval/run_sample.py --ids eval/sample/ids_pilot.txt --dry
    python eval/run_sample.py --ids eval/sample/ids_pilot.txt --out pilot_run1.json

--dry prints how many problems would run and exits: no model calls, no key needed.
A real run needs GEMINI_API_KEY (free key: aistudio.google.com/apikey).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "engine"))

import run_benchmark as rb  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", required=True, help="text file with one problem ID per line")
    ap.add_argument("--out", default=None, help="where to write the results JSON")
    ap.add_argument("--provider", default="gemini", choices=["gemini", "ollama", "claude"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--dry", action="store_true", help="count the selected problems and exit")
    args = ap.parse_args()

    with open(args.ids, encoding="utf-8") as f:
        ids = {line.strip() for line in f if line.strip()}
    subjects = sorted({i.rsplit("-", 1)[0] for i in ids})

    original_load = rb.load

    def load_selected(subject):
        df = original_load(subject)
        keep = df["index"].map(lambda i: f"{subject}-{i}" in ids)
        return df[keep]

    rb.load = load_selected  # full_run looks up `load` at call time, so this takes effect

    selected = {s: len(load_selected(s)) for s in subjects}
    found = sum(selected.values())
    print(f"IDs in file: {len(ids)}; found in the CSVs: {found}")
    for s, n in selected.items():
        print(f"  {s}: {n}")
    if found != len(ids):
        sys.exit("Some IDs were not found. Re-run make_sample_ids.py against the same CSVs.")
    print(f"Estimated time at 6.5 s per call: about {found * 6.5 / 60:.0f} minutes")
    if args.dry:
        return
    if not args.out:
        sys.exit("--out is required for a real run")

    if args.provider == "gemini":
        if not os.environ.get("GEMINI_API_KEY"):
            sys.exit("GEMINI_API_KEY not set (free key: aistudio.google.com/apikey)")
        from parse import GeminiLLM
        llm = GeminiLLM(model=args.model) if args.model else GeminiLLM()
    elif args.provider == "ollama":
        from parse import OllamaLLM
        llm = OllamaLLM(model=args.model) if args.model else OllamaLLM()
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY not set")
        from parse import ClaudeLLM
        llm = ClaudeLLM(model=args.model) if args.model else ClaudeLLM()

    rb.full_run(subjects, None, llm, args.provider, args.out)

    # Record which ID list produced this file, so the result can be traced.
    try:
        with open(args.out, encoding="utf-8") as f:
            data = json.load(f)
        data["summary"]["meta"]["ids_file"] = os.path.basename(args.ids)
        data["summary"]["meta"]["n_ids"] = len(ids)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:  # never lose a finished run over a bookkeeping step
        print(f"(could not add the ID-list note to {args.out}: {e})")


if __name__ == "__main__":
    main()
