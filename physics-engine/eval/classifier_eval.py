"""
Classifier evaluation -- how accurately does the MODEL tag topic and subtopic?

    python3 eval/classifier_eval.py --dry-run     # build the answer key only (no model calls)
    python3 eval/classifier_eval.py               # run the model (needs GEMINI_API_KEY)
    python3 eval/classifier_eval.py --out results.json
    python3 eval/classifier_eval.py --model gemini-3.7-flash --limit 20 --out day1.json
    python3 eval/classifier_eval.py --model gemini-3.7-flash --start 20 --out day2.json
    python3 eval/classifier_eval.py --combine day1.json day2.json

--model pins ONE model with no fallback, so the accuracy belongs to that model alone.
--start/--limit split a run (the free tier allows 20 requests per model per day).

THE ANSWER KEY comes from formula_kb.py itself, never from hand labels: each problem is run
through the engine with its known values, and if the engine solves it through exactly one
formula card (route "deterministic_script"), that card's topic and subtopic are the truth.
A problem the engine can't pin to one card is LEFT OUT and reported, not guessed.

WHAT IS MEASURED is the model on its own: classify() is called WITHOUT the engine's
solution, so the card shortcut is off. With it on, these problems would score 100% by
construction, which would prove nothing about problems the engine can't solve.

Problems: the 16 golden-set problems (golden_set/golden_set_16.csv) plus one problem for
each of the 15 cards the golden set doesn't cover, so all 31 cards are represented.

Grade level and difficulty have no answer key yet; their distribution is reported only.
"""
import argparse
import csv
import json
import os
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))

from scipy import constants as C          # noqa: E402

from classifier import classify, ClassifyError, GeminiClassifierLLM   # noqa: E402
from pipeline import solve_physics_problem                           # noqa: E402

G, K_E, g = C.G, 1 / (4 * C.pi * C.epsilon_0), 9.8

# Known values for the golden-set problems (same values as eval/demo.py), keyed by problem id.
GOLDEN_KNOWNS = {
    "MECH-001": ("Mechanics", dict(v0=0, a=2.5, t=12), ["v", "s"]),
    "MECH-002": ("Mechanics", dict(v0=25, theta_deg=40, g=g), ["t_flight", "h_max", "range_"]),
    "MECH-003": ("Mechanics", dict(m1=4, m2=6, g=g), ["a", "T"]),
    "MECH-004": ("Mechanics", dict(theta_deg=30, mu=0.2, g=g, d=4), ["a", "v"]),
    "MECH-005": ("Mechanics", dict(m=2, k=500, x=0.15), ["v"]),
    "MECH-006": ("Mechanics", dict(m1=3, v1=4, m2=5), ["vf", "KEi", "KEf", "dKE"]),
    "MECH-007": ("Mechanics", dict(M=2, R=0.25, tau=0.6, t=5), ["I", "alpha", "omega"]),
    "MECH-008": ("Mechanics", dict(G=G, M=5.972e24, h=500e3, Re=6.371e6), ["r", "v", "T"]),
    "EM-001": ("E&M", dict(k_e=K_E, q1_abs=3e-6, q2_abs=5e-6, r=0.2), ["F"]),
    "EM-002": ("E&M", dict(k_e=K_E, Q=8e-6, r=0.5), ["E"]),
    "EM-003": ("E&M", dict(k_e=K_E, Q=4e-6, R=0.1, r_in=0.05, r_out=0.3), ["E_in", "E_out"]),
    "EM-004": ("E&M", dict(R1=4, R2=6, R3=12, V=12), ["R_series", "R_eq", "I_total", "I_branch1", "I_branch2"]),
    "EM-005": ("E&M", dict(R=2000, C=100e-6, V0=9), ["tau", "Vc"]),
    "EM-006": ("E&M", dict(q=C.elementary_charge, m=C.proton_mass, v=2e6, B=0.5), ["r", "T"]),
    "EM-007": ("E&M", dict(B=0.8, I=5, L=0.3, theta_deg=90), ["F"]),
    "EM-008": ("E&M", dict(r=0.05, dBdt=0.2), ["A", "EMF"]),
}

# One problem for each card the golden set doesn't cover: (id, text, topic hint, knowns, unknowns).
EXTRA = [
    ("WAVE-01", "A wave has a frequency of 50 Hz and a wavelength of 2 m. Find its speed.",
     "Mechanics", dict(f=50, lambda_=2), ["v"]),
    ("WAVE-02", "A wave is described by y = 0.05 sin(4x - 20t) in SI units. Find its wavelength, "
                "frequency, speed and period.",
     "Mechanics", dict(k_wave=4, omega=20), ["lambda_", "f", "v", "T_period"]),
    ("WAVE-03", "A 0.5 kg mass hangs from a spring of constant 200 N/m. Find the period of its oscillation.",
     "Mechanics", dict(m=0.5, k=200), ["T_period"]),
    ("WAVE-04", "A particle moves as x(t) = 0.4 sin(wt) + 0.3 cos(wt) metres. Find the amplitude of the motion.",
     "Mechanics", dict(coef_sin=0.4, coef_cos=0.3), ["A_amp"]),
    ("WAVE-05", "A 2 kg mass is attached to a spring with k = 50 N/m. What damping coefficient makes the "
                "motion critically damped?",
     "Mechanics", dict(m=2, k=50), ["c_damp"]),
    ("WAVE-06", "An ambulance siren emits 700 Hz while moving toward a stationary listener at 30 m/s. "
                "The speed of sound is 343 m/s. What frequency does the listener hear?",
     "Mechanics", dict(f_source=700, v_sound=343, v_observer=0, v_source=30), ["f_observed"]),
    ("WAVE-07", "A pipe open at both ends is 0.85 m long and the speed of sound is 340 m/s. "
                "Find its fundamental frequency.",
     "Mechanics", dict(v=340, L=0.85, n_harmonic=1), ["f"]),
    ("WAVE-08", "A pipe closed at one end is 0.85 m long and the speed of sound is 340 m/s. "
                "Find its fundamental frequency.",
     "Mechanics", dict(v=340, L=0.85, n_harmonic=1), ["f"]),
    ("GRAV-01", "Find the escape velocity from the surface of the Moon (mass 7.35e22 kg, radius 1.737e6 m).",
     "Mechanics", dict(G=G, M=7.35e22, R=1.737e6), ["v_escape"]),
    ("THERMO-01", "Two moles of an ideal gas occupy 0.05 m^3 at a pressure of 100 kPa. Find its temperature.",
     "Thermodynamics", dict(P=1e5, V=0.05, n_moles=2, R_gas=8.314), ["T_temp"]),
    ("THERMO-02", "How much heat is needed to raise the temperature of 2 kg of water by 30 K? "
                  "The specific heat of water is 4186 J/(kg K).",
     "Thermodynamics", dict(m=2, c_specific=4186, delta_T=30), ["Q_heat"]),
    ("THERMO-03", "How much heat is needed to melt 0.5 kg of ice at 0 C? The latent heat of fusion is 334 kJ/kg.",
     "Thermodynamics", dict(m=0.5, L_latent=334e3), ["Q_heat"]),
    ("THERMO-04", "A heat engine operates between reservoirs at 500 K and 300 K. What is its maximum "
                  "possible efficiency?",
     "Thermodynamics", dict(T_hot=500, T_cold=300), ["efficiency"]),
    ("THERMO-05", "1500 J of heat flows into a system that stays at a constant 300 K. Find its change in entropy.",
     "Thermodynamics", dict(Q_heat=1500, T_temp=300), ["delta_S"]),
    ("THERMO-06", "A gas absorbs 500 J of heat and does 200 J of work on its surroundings. Find the change "
                  "in its internal energy.",
     "Thermodynamics", dict(Q_heat=500, W_work=200), ["delta_U"]),
]


def build_answer_key():
    """Returns (items, excluded). Each item: id, text, true topic/subtopic, card id."""
    rows = list(csv.DictReader(open(os.path.join(HERE, "..", "golden_set", "golden_set_16.csv"))))
    problems = [(r["problem_id"], r["problem_text"], *GOLDEN_KNOWNS[r["problem_id"]]) for r in rows]
    problems += EXTRA
    from formula_kb import ALL_CARDS
    cards = {c.id: c for c in ALL_CARDS}

    items, excluded = [], []
    for pid, text, hint, knowns, unknowns in problems:
        sol = solve_physics_problem(pid, text, knowns, unknowns, topic_hint=hint)
        if sol["route"] != "deterministic_script":
            excluded.append((pid, sol["route"]))
            continue
        card = cards[sol["retrieve"]["matched"]]
        items.append({"id": pid, "text": text, "card": card.id,
                      "true_topic": card.topic, "true_subtopic": card.subtopic})
    return items, excluded


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="build the answer key only; no model calls")
    ap.add_argument("--pause", type=float, default=4.0, help="seconds between model calls (free-tier pacing)")
    ap.add_argument("--out", help="write per-problem results to this JSON file")
    ap.add_argument("--model", help="pin one model, no fallback (e.g. gemini-3.7-flash)")
    ap.add_argument("--start", type=int, default=0, help="skip the first N problems")
    ap.add_argument("--limit", type=int, help="run at most N problems")
    ap.add_argument("--combine", nargs="+", metavar="JSON", help="summarise saved result files together")
    args = ap.parse_args()

    if args.combine:
        results = [r for path in args.combine for r in json.load(open(path))]
        ids = [r["id"] for r in results]
        if len(ids) != len(set(ids)):
            sys.exit("the files overlap: some problems appear twice")
        print(f"Combined {len(args.combine)} files: {len(results)} problems")
        summarize(results)
        return

    items, excluded = build_answer_key()
    covered = {i["card"] for i in items}
    print(f"Answer key: {len(items)} problems covering {len(covered)} formula cards")
    for pid, route in excluded:
        print(f"  left out {pid}: engine route '{route}' (no single card, so no trustworthy label)")
    if args.dry_run:
        for i in items:
            print(f"  {i['id']:10} -> {i['true_topic']} / {i['true_subtopic']}  ({i['card']})")
        return

    llm = GeminiClassifierLLM(models=[args.model]) if args.model else GeminiClassifierLLM()
    chosen = items[args.start: args.start + args.limit if args.limit else None]
    print(f"Running {len(chosen)} problems ({args.start + 1}-{args.start + len(chosen)} of {len(items)})"
          f" with {args.model or 'the default model chain'}")
    results = []
    for n, item in enumerate(chosen):
        if n:
            time.sleep(args.pause)
        try:
            r = classify(item["text"], solution=None, llm=llm)   # card shortcut OFF on purpose
            got = {"topic": r.topic, "subtopic": r.subtopic, "grade_level": r.grade_level,
                   "difficulty": r.difficulty, "confidence": r.confidence, "model": r.model,
                   "needs_review": r.needs_review, "error": None}
        except ClassifyError as e:
            got = {"topic": None, "subtopic": None, "grade_level": None, "difficulty": None,
                   "confidence": None, "model": None, "needs_review": None, "error": str(e)[:120]}
        got["topic_ok"] = got["topic"] == item["true_topic"]
        got["pair_ok"] = got["topic_ok"] and got["subtopic"] == item["true_subtopic"]
        results.append({**item, **got})
        mark = "OK  " if got["pair_ok"] else ("TOPIC" if got["topic_ok"] else ("ERR " if got["error"] else "MISS"))
        print(f"  [{mark}] {item['id']:10} truth {item['true_topic']} / {item['true_subtopic']:22} "
              f"got {got['topic']} / {got['subtopic']}  ({got['model']})")

    summarize(results)
    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nPer-problem results -> {args.out}")


def summarize(results):
    tagged = [r for r in results if r["error"] is None]
    n = len(tagged)
    print("\n" + "=" * 70)
    print(f"Problems: {len(results)}  |  tagged: {n}  |  failed to tag: {len(results) - n}")
    if n:
        print(f"Topic accuracy:    {sum(r['topic_ok'] for r in tagged)}/{n} "
              f"({sum(r['topic_ok'] for r in tagged) / n:.0%})")
        print(f"Subtopic accuracy: {sum(r['pair_ok'] for r in tagged)}/{n} "
              f"({sum(r['pair_ok'] for r in tagged) / n:.0%})  (topic AND subtopic right)")
        print(f"Answered 'Other':  {sum(r['topic'] == 'Other' for r in tagged)}")
        print("\nBy true topic:")
        for t in sorted({r["true_topic"] for r in tagged}):
            rows = [r for r in tagged if r["true_topic"] == t]
            print(f"  {t:15} topic {sum(r['topic_ok'] for r in rows)}/{len(rows)}   "
                  f"subtopic {sum(r['pair_ok'] for r in rows)}/{len(rows)}")
        misses = [r for r in tagged if not r["pair_ok"]]
        if misses:
            print("\nMistakes:")
            for r in misses:
                print(f"  {r['id']:10} truth {r['true_topic']} / {r['true_subtopic']}  ->  got {r['topic']} / {r['subtopic']}")
        print("\nGrade level (no answer key yet):", dict(Counter(r["grade_level"] for r in tagged)))
        print("Difficulty  (no answer key yet):", dict(Counter(r["difficulty"] for r in tagged)))
        print("Models used:", dict(Counter(r["model"] for r in tagged)))


if __name__ == "__main__":
    main()
