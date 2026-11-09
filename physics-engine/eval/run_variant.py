"""
Run a list of problems with a parser prompt read from a file, without editing the shared
engine/parse.py. Everything else is the same as run_sample.py, so results files compare
directly.

Run from physics-engine/:
    python eval/run_variant.py --export-prompt eval/prompts/v0.txt          (start point)
    python eval/run_variant.py --ids eval/sample/ids_ab.txt --prompt-file eval/prompts/v0.txt --dry
    python eval/run_variant.py --ids eval/sample/ids_ab.txt --prompt-file eval/prompts/v0.txt \
        --out benchmark_ab_v0.json --model gemini-flash-lite-latest

The prompt file must contain the two placeholders {glossary} and {problem}. Literal braces
(the JSON example in the prompt) must be doubled, {{ and }}; --export-prompt writes the
current prompt in exactly that form, so edit a copy of it.
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "engine"))

import run_benchmark as rb  # noqa: E402
import parse  # noqa: E402


def check_prompt(text):
    if "{glossary}" not in text or "{problem}" not in text:
        sys.exit("The prompt must contain both {glossary} and {problem}.")
    try:
        text.format(glossary="GLOSSARY", problem="PROBLEM")
    except (KeyError, IndexError, ValueError) as e:
        sys.exit(f"The prompt does not format ({type(e).__name__}: {e}). Double any literal braces: {{{{ and }}}}.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids")
    ap.add_argument("--prompt-file")
    ap.add_argument("--out")
    ap.add_argument("--model", default=None)
    ap.add_argument("--provider", default="gemini", choices=["gemini", "ollama", "claude"])
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--export-prompt", help="write the current PARSE_PROMPT to this file and exit")
    args = ap.parse_args()

    if args.export_prompt:
        os.makedirs(os.path.dirname(os.path.abspath(args.export_prompt)), exist_ok=True)
        with open(args.export_prompt, "w", encoding="utf-8") as f:
            f.write(parse.PARSE_PROMPT)
        print(f"Wrote the current prompt to {args.export_prompt}")
        return
    if not (args.ids and args.prompt_file):
        sys.exit("--ids and --prompt-file are required")

    with open(args.prompt_file, encoding="utf-8") as f:
        prompt = f.read()
    check_prompt(prompt)
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:10]
    same = prompt == parse.PARSE_PROMPT
    print(f"Prompt file: {args.prompt_file} (sha256 {digest}); identical to the engine's current prompt: {same}")

    with open(args.ids, encoding="utf-8") as f:
        ids = {line.strip() for line in f if line.strip()}
    subjects = sorted({i.rsplit("-", 1)[0] for i in ids})
    original_load = rb.load

    def load_selected(subject):
        df = original_load(subject)
        return df[df["index"].map(lambda i: f"{subject}-{i}" in ids)]

    rb.load = load_selected
    found = sum(len(load_selected(s)) for s in subjects)
    print(f"IDs in file: {len(ids)}; found in the CSVs: {found}; about {found * 6.5 / 60:.0f} minutes")
    if found != len(ids):
        sys.exit("Some IDs were not found.")
    if args.dry:
        return
    if not args.out:
        sys.exit("--out is required for a real run")

    parse.PARSE_PROMPT = prompt  # parse_problem reads this module attribute at call time

    if args.provider == "gemini":
        if not os.environ.get("GEMINI_API_KEY"):
            sys.exit("GEMINI_API_KEY not set")
        llm = parse.GeminiLLM(model=args.model) if args.model else parse.GeminiLLM()
    elif args.provider == "ollama":
        llm = parse.OllamaLLM(model=args.model) if args.model else parse.OllamaLLM()
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY not set")
        llm = parse.ClaudeLLM(model=args.model) if args.model else parse.ClaudeLLM()

    rb.full_run(subjects, None, llm, args.provider, args.out)

    try:
        with open(args.out, encoding="utf-8") as f:
            data = json.load(f)
        data["summary"]["meta"].update(ids_file=os.path.basename(args.ids), prompt_file=os.path.basename(args.prompt_file),
                                       prompt_sha256=digest)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        print(f"(could not add the prompt note to {args.out}: {e})")


if __name__ == "__main__":
    main()
