# Automated assessment: what the benchmarks can and can't tell us

Sri asked for automated assessment against physics benchmarks. Here is what happened when
that was actually run, including a finding that changes what to build next.

Reproduce with no API key and no cost:
```bash
python3 eval/run_benchmark.py --dry-run
```

## The benchmark, and the honest denominator

**UGPhysics** (ICML 2025) is the right benchmark for our scope — undergraduate level, with
separate Classical Mechanics (836 problems) and Classical Electromagnetism (390) subsets.
Both are pulled and in hand. GPQA, OlympiadBench and PHYBench were checked and ruled out:
graduate/olympiad level, too hard to say anything useful about a 16-card intro library yet.

Then the part worth knowing before spending anything on evaluation:

| | Problems | Share |
|---|---|---|
| Symbolic ground truth (expression, equation, T/F, interval, multiple choice) | 734 | 59.9% |
| Typed numeric, but no number actually readable (bare symbols like `A`) | 258 | 21.0% |
| **Fully numeric — scorable against the engine as it stands** | **224** | **18.3%** |
| Partially numeric | 10 | 0.8% |

**Only 18% of this benchmark can score the engine today.** Not because the engine fails the
other 82%, but because those problems ask for something it doesn't yet produce.

## What the other 82% is asking for

Most of UGPhysics wants a **derivation** — an answer like

```
v = (k/(c−b))·e^(−bt) − g/c
```

not a number. That's what undergraduate physics largely tests. Our engine returns numbers,
because the formula cards substitute numeric values *before* SymPy sees the equations.

**Those two facts are the same fact, and this has now been built.** Cards no longer bake
numbers into their equations — they stay symbolic and numbers substitute last. All 16 cards
now return a general formula alongside the number:

```
MECH-DYN-ATWOOD     T = 2*g*m1*m2/(m1 + m2)        a = g*(m2 - m1)/(m1 + m2)
MECH-GRAV-ORBIT     v = sqrt(G*M/(Re + h))         T = 2*pi*(Re + h)/sqrt(G*M/(Re + h))
EM-CIRC-RC          tau = C*R                      Vc = V0*(1 - exp(-1))
```

**Honest scope on what that unlocks.** The *engine-side* blocker is gone — it now produces
exactly the kind of answer 60% of the benchmark asks for. The *harness-side* blocker
remains: comparing our symbolic answer to the benchmark's requires parsing its boxed LaTeX
into SymPy, which needs the antlr4 runtime (unavailable in this build environment). So the
scorable fraction hasn't moved yet in practice. Half the problem is solved, not all of it,
and saying "4× unlocked" would be overclaiming.

**Three things improved, not one:**
1. Symbolic answers — what most of the benchmark actually asks for.
2. Unit propagation is now possible — the equations still carry symbols when SymPy sees them.
3. **Tutor hints got materially better**, which wasn't anticipated. A hint used to read
   `T - 39.2 = 4*a` — arithmetic already leaked. It now reads `T - g*m1 = a*m1`, teaching
   the relationship, followed by a new rung showing the rearranged general formula before
   the numeric answer. That's the actual pedagogical progression.

**And it's 43% faster.** Solving symbolically costs ~290ms, so doing it per problem was a
26× slowdown. Solving once per card and caching the result — including the `simplify()`
call, which was the real cost once measured — brings steady state to **6.30 ms/problem
versus 11.04 ms before**, because substituting into a pre-solved expression beats
re-solving from scratch every time.

## Where the scorable problems live

| Topic | Scorable / Total | |
|---|---|---|
| Vibrations and Waves | 76 / 179 | **42.5%** |
| Circuit Analysis | 24 / 58 | 41.4% |
| Fluid Mechanics | 18 / 77 | 23.4% |
| Particle Dynamics | 44 / 322 | 13.7% |
| Rigid-Body Dynamics | 22 / 180 | 12.2% |
| Electrostatics | 20 / 184 | 10.9% |
| Magstatics | 14 / 148 | 9.5% |
| Central Force Motion | 6 / 78 | 7.7% |

**Vibrations and Waves is the most scorable topic and has zero formula cards.** It was
locked into scope on Aug 3 and never built. It's also 179 problems — the fourth largest
topic. Biggest gap, most measurable, already in scope: the SHM card is the unambiguous next
build, and now for three independent reasons rather than one.

## On sample size, since "run it on everything" is the intuitive move

Sample size for a confidence interval barely depends on population size. Roughly 1,100
well-stratified problems gives ±3% at 95% confidence whether you're drawing from 10,000 or
10 million. Running a million problems costs about a thousand times more than running
eleven hundred and tells you almost nothing extra.

The cost is entirely in the reading stage: the solver runs at ~11ms/problem (1M problems =
12 minutes on 16 cores, effectively free), but each problem needs one model call at ~1,064
input tokens — putting 1M problems near **$5,400**. Stratified sampling per topic is both
cheaper and more useful, since it yields per-topic accuracy rather than one global number.

## What's built and what's still blocked

**Built and testable now (`eval/answer_match.py`):** the comparison layer, which is the
unglamorous part that gates every accuracy number. `3.27` vs `3.2667` vs `\frac{49}{15}` vs
`2.876 × 10^5` vs `3.04 \text{m}` all have to compare correctly, in any order, across
multi-answer rows. Getting this wrong scores a correct engine as wrong and produces a
confidently meaningless accuracy figure — the project's own failure mode, one level up in
the evaluation harness. Tested against real UGPhysics formats.

**Written but not executed here — run this and find out.** Comparing our symbolic answer to
the benchmark's boxed LaTeX needs SymPy's `parse_latex`, which requires one install:

```bash
pip install antlr4-python3-runtime==4.11
python3 eval/run_benchmark.py --limit 200
```

`compare_symbolic()` in `eval/answer_match.py` does the comparison, and it's wired into the
full run. It compares by simplifying the difference to zero rather than by string match —
`g*(m2-m1)/(m1+m2)` and `-g*(m1-m2)/(m1+m2)` are the same answer written two ways, and a
string comparison would score that wrong. That logic is tested; the `parse_latex` call
itself is not, because it wasn't installable in the environment this was written in. So
treat the symbolic path as **untested-but-ready**, not verified.

The honest consequence: the 18% figure above counts only the numeric path, so it's a floor,
not a ceiling. Whether the symbolic path lifts it substantially is a question the command
above answers and I can't.

**Run it for free — no credit card.** Parse is the only stage needing a model, and it
doesn't need a frontier one; it's structured extraction, not hard reasoning. Google AI
Studio's free tier requires no card and doesn't expire (~1,500 requests/day on Flash, far
more than a benchmark run needs):

```bash
# 1. Free key at https://aistudio.google.com  ->  Get API key
export GEMINI_API_KEY=...
pip install antlr4-python3-runtime==4.11        # enables symbolic comparison
python3 eval/run_benchmark.py --subject ClassicalMechanics --limit 100
```

Fully local alternative, no key and no network at all:
```bash
brew install ollama && ollama serve
ollama pull llama3.2
python3 eval/run_benchmark.py --provider ollama --limit 50
```

A paid Anthropic key still works via `--provider claude`, but nothing here requires it.

**One data-governance note, consistent with Q6.** Google may use free-tier prompts to
improve their products. Fine for UGPhysics, which is public benchmark data. **Not** fine for
student work — if this ever points at real student submissions, use a paid tier or Ollama,
where nothing leaves the machine.
