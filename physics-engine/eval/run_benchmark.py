"""
AUTOMATED BENCHMARK RUNNER -- UGPhysics vs. the engine.

Two modes, because one of them needs no API key and answers a question worth
answering first:

  --dry-run   Reports how much of the benchmark is even SCORABLE against a
              numeric engine, with no model calls and no cost. Run this first.
              It answers "can this benchmark measure us at all?" before spending
              anything finding out how well we do.

  (default)   Full evaluation: parse -> solve -> compare. Needs a model key
              (GEMINI_API_KEY by default; see --provider).

Usage:
    python3 eval/run_benchmark.py --dry-run
    python3 eval/run_benchmark.py --provider ollama --model qwen2.5:7b --limit 40
    python3 eval/run_benchmark.py --limit 200
    python3 eval/run_benchmark.py --subject ClassicalElectromagnetism --limit 100

Data: run eval/pull_ugphysics_subset.py first (needs network). The CSVs are
gitignored -- UGPhysics is CC-BY-NC-SA-4.0 (NonCommercial), so the data stays
local and only the resulting NUMBERS travel.
"""
import argparse
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
sys.path.insert(0, HERE)

import pandas as pd  # noqa: E402

from answer_match import (  # noqa: E402
    compare_symbolic,
    compare, strip_boxed, split_answers, to_number, Verdict,
)

SYMBOLIC_TYPES = {"EX", "EQ", "TF", "IN", "MC"}
# Question types the engine cannot answer at all: it returns numbers and formulas,
# not yes/no or a choice letter. Skipped before parse so they don't cost a model call
# or show up as false "no card" declines.
OUT_OF_SCOPE_TYPES = {"TF", "MC"}


def load(subject):
    path = os.path.join(HERE, f"ugphysics_{subject}.csv")
    if not os.path.exists(path):
        sys.exit(f"missing {path}\nRun eval/pull_ugphysics_subset.py first "
                 f"(needs network access).")
    return pd.read_csv(path)


def classify_scorability(row):
    """Can this row score a NUMERIC engine at all? No model calls needed."""
    types = {t.strip().split()[0] for t in str(row["answer_type"]).split(",") if t.strip()}
    if types & SYMBOLIC_TYPES:
        return "symbolic", sorted(types)
    nums = [to_number(t) for t in split_answers(strip_boxed(row["answers"]))]
    if not nums or all(n is None for n in nums):
        return "no_number_readable", None
    if any(n is None for n in nums):
        return "partially_numeric", None
    return "scorable", None


def dry_run(subjects):
    """What fraction of this benchmark can measure us, and what is the rest asking for?"""
    print("=" * 74)
    print("DRY RUN -- what fraction of the benchmark can score a numeric engine?")
    print("(no model calls, no cost)")
    print("=" * 74)
    grand = Counter()
    per_topic = {}
    for subject in subjects:
        df = load(subject)
        c = Counter()
        for _, row in df.iterrows():
            kind, _ = classify_scorability(row)
            c[kind] += 1
            grand[kind] += 1
            t = row["topic"]
            per_topic.setdefault(t, Counter())[kind] += 1
        total = sum(c.values())
        print(f"\n{subject} ({total} problems)")
        for k, v in c.most_common():
            print(f"   {v:5} ({v/total:5.1%})  {k}")

    tot = sum(grand.values())
    print("\n" + "-" * 74)
    print(f"ACROSS BOTH SUBJECTS ({tot} problems)")
    for k, v in grand.most_common():
        print(f"   {v:5} ({v/tot:5.1%})  {k}")
    scorable = grand["scorable"]
    print(f"\nScorable against the engine as it stands: {scorable}/{tot} ({scorable/tot:.1%})")
    print("\nBy topic (scorable / total):")
    for t, c in sorted(per_topic.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(c.values())
        print(f"   {c['scorable']:4} / {n:4}  ({c['scorable']/n:5.1%})  {t}")

    print("\n" + "=" * 74)
    print("WHAT THE UNSCORABLE MAJORITY IS ASKING FOR, AND WHERE WE STAND")
    print("=" * 74)
    print("Most of this benchmark wants a DERIVATION -- a symbolic expression like")
    print("  v = (k/(c-b))e^(-bt) - g/c")
    print("not a number. That is what undergraduate physics largely tests.")
    print()
    print("ENGINE SIDE: done. Cards now stay symbolic until a final substitution, so all")
    print("16 return a general formula alongside the number (T = 2*g*m1*m2/(m1+m2), and")
    print("so on). The engine produces exactly the shape of answer these problems want.")
    print()
    print("HARNESS SIDE: one install away. Comparing our formula against the benchmark's")
    print("boxed LaTeX needs sympy's parse_latex, which requires:")
    print("    pip install antlr4-python3-runtime==4.11")
    print("The comparison code is written (eval/answer_match.py: compare_symbolic) and")
    print("wired into the full run. It was not executable in the environment it was")
    print("written in, so treat the symbolic path as untested-but-ready rather than")
    print("verified -- run it and see.")
    print()
    print("So the 'scorable' figure above is the floor, not the ceiling: it counts only")
    print("the numeric path. With antlr4 installed the symbolic majority is attempted too.")


# ---------------------------------------------------------------------------
# Full run: one row per problem, one outcome per row
# ---------------------------------------------------------------------------
# Every problem the run looks at gets exactly ONE of these outcomes, and exactly one
# row in the results file. The summary is computed FROM the rows, so the two can
# never disagree again.
#
# Earlier versions had two bugs here:
#   1. a parse failure was scored as a MISMATCH, i.e. a wrong answer. The engine
#      never produced an answer, so "0% accuracy" was an artefact of the scoring.
#   2. problems with unreadable ground truth were counted in the summary but never
#      written as rows (40 in the summary, 32 rows).
class Outcome:
    SKIPPED = "skipped_unreadable_truth"     # benchmark answer itself can't be read
    OUT_OF_SCOPE = "skipped_question_type"   # yes/no or multiple choice: engine can't answer these
    NOTHING_TO_SOLVE = "parse_found_no_unknown"  # parse ran but found nothing to solve for
    PARSE_API = "parse_failed_api"           # model call failed (quota, network, auth)
    PARSE_BAD = "parse_failed_bad_output"    # model answered, but not usable JSON
    SOLVE_ERROR = "solve_error"              # engine raised an exception
    NO_CARD = "declined_no_card"             # no card solves for the requested unknown
    MISSING_KNOWNS = "declined_missing_knowns"  # a card fits the unknown, knowns don't close it
    AMBIGUOUS = "ambiguous"                  # several cards closed and disagree
    MATCH = "match"                          # answered, matches ground truth
    MISMATCH = "mismatch"                    # answered, does NOT match -- a real wrong answer
    NOT_COMPARED = "answered_not_compared"   # answered, but ground truth couldn't be compared


_API_FAILURE_PREFIXES = ("Gemini call failed", "GEMINI_API_KEY not set", "Ollama call failed")
# Stop early if the model is clearly unreachable (e.g. quota used up), instead of
# burning through the rest of the subset and recording hundreds of identical failures.
MAX_CONSECUTIVE_API_FAILURES = 3


def _jsonable(d):
    """Parse output holds sympy objects; store them as readable strings."""
    if d is None:
        return None
    if isinstance(d, dict):
        return {str(k): _jsonable(v) for k, v in d.items()}
    if isinstance(d, (list, tuple)):
        return [_jsonable(v) for v in d]
    if isinstance(d, (int, float, str, bool)):
        return d
    return str(d)


def _parse_record(parsed):
    """What the model actually read. This is what lets us tell a parse problem apart
    from a coverage gap: a decline with unrecognized variable names, or with an
    obviously missing known, points at parse; a clean parse with no card points at
    coverage."""
    norm = parsed.get("normalization") or {}
    return {
        "knowns": _jsonable(parsed.get("knowns")),
        "unknowns": _jsonable(parsed.get("unknowns")),
        "topic_hint": parsed.get("topic_hint"),
        "injected_constants": _jsonable(parsed.get("injected")),
        "unrecognized_names": _jsonable(norm.get("unrecognized", [])),
        "renamed": _jsonable(norm.get("renamed", {})),
        "json_repaired": bool(parsed.get("json_repaired", False)),
        "coerced_text_values": _jsonable(parsed.get("coerced_to_value_or_symbol", {})),
        "formula_given_as_value": _jsonable(parsed.get("formula_given_as_value", {})),
    }


def _summarize(rows, meta):
    """All numbers come from the rows. Denominators are stated next to every rate."""
    c = Counter(r["outcome"] for r in rows)
    seen = len(rows)
    attempted = seen - c[Outcome.SKIPPED] - c[Outcome.OUT_OF_SCOPE]
    parse_failed = c[Outcome.PARSE_API] + c[Outcome.PARSE_BAD]
    parsed_ok = attempted - parse_failed
    answered = c[Outcome.MATCH] + c[Outcome.MISMATCH] + c[Outcome.NOT_COMPARED]
    compared = c[Outcome.MATCH] + c[Outcome.MISMATCH]
    declined = c[Outcome.NO_CARD] + c[Outcome.MISSING_KNOWNS]
    declined_unrecognized = sum(
        1 for r in rows
        if r["outcome"] in (Outcome.NO_CARD, Outcome.MISSING_KNOWNS)
        and (r.get("parse") or {}).get("unrecognized_names"))

    def rate(num, den):
        return round(num / den, 4) if den else None

    return {
        "meta": meta,
        "counts": {k: c[v] for k, v in vars(Outcome).items() if not k.startswith("_")},
        "seen": seen,
        "attempted": attempted,
        "parse_failed": parse_failed,
        "parsed_ok": parsed_ok,
        "declined": declined,
        "declined_with_unrecognized_names": declined_unrecognized,
        "parsed_only_after_json_repair": sum(
            1 for r in rows if (r.get("parse") or {}).get("json_repaired")),
        "ambiguous": c[Outcome.AMBIGUOUS],
        "answered": answered,
        "compared": compared,
        "wrong_answers": c[Outcome.MISMATCH],
        "rates": {
            "parse_success  (parsed_ok / attempted)": rate(parsed_ok, attempted),
            "answer_rate    (answered / attempted)": rate(answered, attempted),
            "accuracy       (match / compared)": rate(c[Outcome.MATCH], compared),
        },
    }


def _print_summary(s):
    m, n = s["meta"], s["counts"]
    print("\n" + "=" * 74)
    print("BENCHMARK RESULT")
    print("=" * 74)
    print(f"  provider / model       : {m['provider']} / {m['model']}   "
          f"seed: {m.get('seed')}   cards: {m['n_cards']}")
    if m.get("aborted"):
        print(f"  RUN STOPPED EARLY      : {m['aborted']}")
    print(f"  problems seen          : {s['seen']}")
    print(f"    skipped (truth unreadable): {n['SKIPPED']}")
    print(f"    skipped (yes/no, choice)  : {n['OUT_OF_SCOPE']}")
    print(f"  attempted              : {s['attempted']}")
    print(f"    parse failed (API)        : {n['PARSE_API']}")
    print(f"    parse failed (bad output) : {n['PARSE_BAD']}")
    print(f"    parsed only after LaTeX/JSON repair: {s['parsed_only_after_json_repair']}")
    print(f"    parse found no unknown    : {n['NOTHING_TO_SOLVE']}")
    print(f"    solve error               : {n['SOLVE_ERROR']}")
    print(f"    declined, no card         : {n['NO_CARD']}")
    print(f"    declined, missing knowns  : {n['MISSING_KNOWNS']}")
    print(f"      of declines, parse had unrecognized names: "
          f"{s['declined_with_unrecognized_names']}")
    print(f"    ambiguous (needs review)  : {n['AMBIGUOUS']}")
    print(f"    answered                  : {s['answered']}")
    print(f"      match                   : {n['MATCH']}")
    print(f"      WRONG                   : {n['MISMATCH']}")
    print(f"      not comparable          : {n['NOT_COMPARED']}")
    acc = s["rates"]["accuracy       (match / compared)"]
    if acc is None:
        print("\n  accuracy: not defined -- no answer could be compared to ground truth.")
        print("  Do NOT report this run as '0% accuracy'.")
    else:
        print(f"\n  accuracy: {acc:.1%} over {s['compared']} compared problems, "
              f"NOT over {s['seen']} seen")


def full_run(subjects, limit, llm, provider, out_path):
    import datetime
    from parse import parse_problem, ParseError
    from pipeline import solve_physics_problem
    from formula_kb import ALL_CARDS

    meta = {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "provider": provider,
        "model": getattr(llm, "model", type(llm).__name__),
        "seed": getattr(llm, "seed", None),
        "subjects": subjects,
        "limit": limit,
        "n_cards": len(ALL_CARDS),
        "aborted": None,
    }
    rows = []
    api_failures_in_a_row = 0

    # Keep the model's last raw reply, so a parse failure row shows WHAT the model
    # actually returned, not only the error message.
    last_reply = {"text": None}

    def recording_llm(prompt):
        last_reply["text"] = None
        last_reply["text"] = llm(prompt)
        return last_reply["text"]

    def add(problem_id, result, **extra):
        rows.append(dict(problem_id=problem_id, outcome=result, **extra))
        print(f"  [{result:26}] {problem_id}", file=sys.stderr)

    try:
        for subject in subjects:
            df = load(subject)
            if limit:
                df = df.head(limit)
            for _, row in df.iterrows():
                kind, _ = classify_scorability(row)
                pid = f"{subject}-{row['index']}"
                truth = str(row["answers"])

                if kind == "no_number_readable":
                    add(pid, Outcome.SKIPPED, kind=kind, truth=truth)
                    continue
                q_types = {t.strip().split()[0] for t in str(row["answer_type"]).split(",")
                           if t.strip()}
                if q_types and q_types <= OUT_OF_SCOPE_TYPES:
                    add(pid, Outcome.OUT_OF_SCOPE, kind=kind, answer_type=str(row["answer_type"]),
                        truth=truth)
                    continue

                try:
                    parsed = parse_problem(str(row["problem"]), recording_llm)
                except Exception as e:
                    # ParseError covers bad model output and Gemini/Ollama call failures.
                    # Anything else (e.g. an anthropic SDK error) is a failed model call.
                    msg = str(e) if isinstance(e, ParseError) else f"{type(e).__name__}: {e}"
                    if not isinstance(e, ParseError) or msg.startswith(_API_FAILURE_PREFIXES):
                        add(pid, Outcome.PARSE_API, kind=kind, detail=msg[:300])
                        api_failures_in_a_row += 1
                        if api_failures_in_a_row >= MAX_CONSECUTIVE_API_FAILURES:
                            meta["aborted"] = (f"{api_failures_in_a_row} model calls failed in a "
                                               f"row (quota or network?). Last error: {msg[:200]}")
                            return
                    else:
                        api_failures_in_a_row = 0
                        add(pid, Outcome.PARSE_BAD, kind=kind, detail=msg[:300],
                            raw_reply=(last_reply["text"] or "")[:1500])
                    continue
                api_failures_in_a_row = 0
                parse_rec = _parse_record(parsed)
                if not parsed.get("unknowns"):
                    add(pid, Outcome.NOTHING_TO_SOLVE, kind=kind, parse=parse_rec,
                        raw_reply=(last_reply["text"] or "")[:1500], truth=truth)
                    continue

                try:
                    sol = solve_physics_problem(pid, str(row["problem"]), parsed["knowns"],
                                                parsed["unknowns"],
                                                topic_hint=parsed.get("topic_hint"))
                except Exception as e:  # one bad problem must not lose the whole run
                    add(pid, Outcome.SOLVE_ERROR, kind=kind, parse=parse_rec,
                        detail=f"{type(e).__name__}: {e}"[:300])
                    continue

                route = sol["route"]
                plan = sol.get("plan") or {}
                considered = (sol.get("retrieve") or {}).get("candidates_considered", [])

                if route == "no_deterministic_path":
                    outcome = Outcome.NO_CARD if not considered else Outcome.MISSING_KNOWNS
                    add(pid, outcome, kind=kind, parse=parse_rec,
                        cards_considered=considered,
                        plan_reason=plan.get("reason"),
                        plan_attempts=_jsonable(plan.get("attempts")),
                        truth=truth)
                    continue

                if route == "ambiguous_multiple_deterministic_paths":
                    cands = (sol.get("solve") or {}).get("per_candidate_results", [])
                    add(pid, Outcome.AMBIGUOUS, kind=kind, parse=parse_rec,
                        candidates=_jsonable([{"card_id": c.get("card_id"),
                                               "answer": c.get("final_answer")} for c in cands]),
                        truth=truth)
                    continue

                # deterministic_script: the engine committed to an answer
                if kind == "symbolic":
                    verdict, detail = compare_symbolic(
                        sol["solve"].get("symbolic_answer"), row["answers"])
                else:
                    verdict, detail = compare(list(sol["final_answer"].values()),
                                              row["answers"], row["answer_type"])
                outcome = {Verdict.MATCH: Outcome.MATCH,
                           Verdict.MISMATCH: Outcome.MISMATCH}.get(verdict, Outcome.NOT_COMPARED)
                add(pid, outcome, kind=kind, parse=parse_rec, detail=detail,
                    card=(sol.get("retrieve") or {}).get("matched"),
                    engine=_jsonable(sol["final_answer"]),
                    engine_symbolic=_jsonable(sol["solve"].get("symbolic_answer")),
                    truth=truth)
    except KeyboardInterrupt:
        meta["aborted"] = "stopped by user (Ctrl+C)"
    finally:
        # Always save what we have, even after a crash or Ctrl+C, so a quota cut-off
        # halfway through a run doesn't throw away the problems already done.
        s = _summarize(rows, meta)
        _print_summary(s)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"summary": s, "rows": rows}, f, indent=2, default=str)
        print(f"\n  per-problem detail -> {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="report scorability only; no model calls, no cost")
    ap.add_argument("--subject", default=None,
                    choices=["ClassicalMechanics", "ClassicalElectromagnetism"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default="benchmark_results.json",
                    help="where to write per-problem results (default: ./benchmark_results.json)")
    ap.add_argument("--provider", default="gemini",
                    choices=["gemini", "ollama", "claude"],
                    help="gemini = FREE tier, no credit card (default). "
                         "ollama = free and fully local. claude = paid.")
    ap.add_argument("--model", default=None,
                    help="model name for the provider, e.g. qwen2.5:7b or llama3.1:8b for "
                         "ollama. Default: the provider's own default.")
    args = ap.parse_args()

    subjects = [args.subject] if args.subject else \
        ["ClassicalMechanics", "ClassicalElectromagnetism"]

    if args.dry_run:
        dry_run(subjects)
    else:
        if args.provider == "gemini":
            if not os.environ.get("GEMINI_API_KEY"):
                sys.exit("GEMINI_API_KEY not set.\n"
                         "  Free key, no credit card: https://aistudio.google.com -> Get API key\n"
                         "  Then: export GEMINI_API_KEY=...\n"
                         "  Or use --provider ollama to run fully local, or --dry-run for "
                         "the no-cost scorability analysis.")
            from parse import GeminiLLM
            llm = GeminiLLM(model=args.model) if args.model else GeminiLLM()
        elif args.provider == "ollama":
            from parse import OllamaLLM
            llm = OllamaLLM(model=args.model) if args.model else OllamaLLM()
        else:
            if not os.environ.get("ANTHROPIC_API_KEY"):
                sys.exit("ANTHROPIC_API_KEY not set. Use --provider gemini for the free tier.")
            from parse import ClaudeLLM
            llm = ClaudeLLM(model=args.model) if args.model else ClaudeLLM()
        full_run(subjects, args.limit, llm, args.provider, args.out)