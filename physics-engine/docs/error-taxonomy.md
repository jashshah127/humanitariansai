# Error-Analysis Taxonomy: Why the Engine Does Not Answer

**Author:** Harsh Gujarathi · **Plan item:** Wk 4, error-analysis taxonomy from Wk 3's parse-accuracy results (planned Oct 26 to Nov 1; written Nov 2, 2026)
**Status:** Draft v1 · **Audience:** Sri, Nik, Jash
No dataset text appears in this document. Problems are referred to by ID.

## 1. Data and method

- **Data:** the numeric stratum of batch 1: 234 UGPhysics problems, run through the real parser (`gemini-flash-lite-latest`) and the engine. Results are in `benchmark_full_01_all.json`.
- **Rule-based sort** (`eval/taxonomy.py`): each decline is grouped by how close the best-fitting card came, counting only quantities the parser actually gave (injected constants such as G and g do not count).
- **Hand reading:** the problem text of 22 problems was read (11 numeric declines, the 3 wrong answers, 6 empty parses, 5 problems from the wave-equation group; some overlap). The model's own notes were read for all 39 "no unknown" problems.
- Both methods are a first sort. The counts are exact; the labels for causes are tested only on the problems read.

## 2. The taxonomy (234 numeric problems)

| # | Group | Count | Share | What it is |
|---|---|---|---|---|
| A | **Parser declined: outside the glossary** | 39 | 17% | The parser found nothing to solve for and said so in its notes |
| B | **No card** | 61 | 26% | The unknown has no card at all |
| C | **Ill-fitting card** | 81 | 35% | The parser gave nothing any considered card uses. The runner labels these "missing knowns" |
| D | **Near miss** | 48 | 21% | A card fits and some quantities are missing: 18 are one short, 30 are several short |
| E | **Answered, wrong** | 3 | 1.3% | Verified badge shown |
| F | **Answered, right** | 2 | 0.9% | |

**Groups A + B + C (181 problems, 77%) are coverage gaps or poor fits, not parser faults.** A parser fix cannot change them. Group C's label hides this: the engine considered a card only because the unknown shares a name with that card's output (`f`, `v`, `a`), then reported "missing knowns".

### A. Parser declined (39): what the model's notes say
The prompt tells the parser to use only glossary names, so when the physics is not in the glossary it returns nothing and says why. Grouping the 39 notes by theme (my reading of the notes; some are truncated):

| Theme | Count |
|---|---|
| Electrostatics or mechanics expressions, line integrals, conceptual questions | 8 |
| Fluids: viscosity, flow, pressure, statics | 7 |
| Inductance and transmission lines | 6 |
| Wave phase, interference, intensity, vibration velocity | 5 |
| Pure mathematics (centroids) | 4 |
| Quality factor and driven oscillators | 3 |
| Rigid body with Euler angles | 2 |
| Other (Kepler, restitution coefficient, rocket equation, charge emission) | 4 |

This is an honest decline: the parser did not invent a value. It also gives a list of glossary and card additions to consider: restitution coefficient, quality factor, phase difference, average power, intensity, viscosity. One problem refers to an earlier numbered problem for its values (ClassicalMechanics-2381) and cannot be solved from its text.

### B. No card (61)
The unknowns are spread thin: `t` 8, `B` 5, then `Q`, `m`, `L`, `V` at 4 each, `C` and `R` at 3. No single card unlocks a large share.

### C. Ill-fitting card (81)
Cards most often considered: `WAVE-FROM-EQUATION` 12, `MECH-DYN-ATWOOD` 12, `MECH-KIN-1D` 10, `EM-ELEC-COULOMB` 8, `MECH-ROT-TORQUE` 7. Of five read from the wave-equation card's group, four had no matching card (a resonance scaling argument, a charged sphere in a field, a collision, a relative-velocity problem) and one was a genuine parser miss (ClassicalMechanics-1544). So this group is mostly coverage with some parser misses mixed in.

### D. Near miss (48)
- **One short (18):** `v_observer` 4 (all Doppler, an observer at rest left unstated), `q2_abs` 2, `Q` 2, then single cases of `dBdt`, `r`, `R`, `coef_cos`, `M`. These are the closest to an answer.
- **Several short (30):** closest cards `MECH-KIN-1D` 9, `EM-CIRC-RC-CHARGE-1TAU` 4, `MECH-ROT-TORQUE` 3, `EM-MAG-FORCE-WIRE` 3, `MECH-GRAV-ORBIT` 3, `WAVE-DOPPLER` 3.

### E. Answered and wrong (3)
| Problem | Cause |
|---|---|
| ClassicalMechanics-1565 | The parser dropped one of two balls and the meeting condition; a single-projectile card answered |
| ClassicalMechanics-1583 | A per-centimetre wave number was converted the wrong way, giving a wave speed 10,000 times too large |
| ClassicalMechanics-1637 | The parser dropped the condition on the damped frequency; the critical-damping card answered |

## 3. Parser-addressable failure modes (candidates for Week 5)

| Mode | Evidence | Size found so far |
|---|---|---|
| Dropped conditions or quantities in multi-part problems | 1565, 1637 (both wrong answers) | 2 confirmed; others not yet looked for |
| Coefficients inside a stated equation not read | 1544, 1643, 1583, 2014 confirmed | 10 numeric problems mention a wave and a sine (7 declined, 1 wrong, 2 no unknown); 5 of them unread |
| Unit conversion of per-length quantities | 1583 | 1 |
| Implied zero (an observer or body at rest) | 4 Doppler problems one quantity short; ClassicalMechanics-1665 shows the sign risk | "at rest" appears in 7 numeric problems (5 declined, 1 no unknown, 1 no card); Doppler counts overlap |
| Glossary name mismatch | ClassicalMechanics-1566: the card needs `R`, the parser wrote `Re` | 1 confirmed |

The sizes add up to roughly 20 to 30 problems, under 13% of the numeric stratum, and not all would become right answers. **A parser change cannot reach most of the 234.** The larger lever is coverage: cards and glossary entries for the themes in group A and the unknowns in group B.

## 4. How Week 5 prompt changes should be tested

1. **Test set:** the target problems from section 3, the 5 problems already answered, and about 20 random controls from groups A to C.
2. **Measure three things, not accuracy:** newly answered problems, how many of those are right, and **how many are wrong**. Any new wrong answer counts against a change.
3. **Stopping rule:** no new wrong answers. Answering more problems means more chances of being confidently wrong. Defaulting an unstated observer speed to zero would, with the parser's current sign handling, turn a decline into a wrong answer on ClassicalMechanics-1665 (1,031 Hz against 971).
4. **Repeat each variant twice.** Outcomes agreed on 89% of shared problems between runs (28 problems), so single runs can move by chance.
5. Fix the model (`gemini-flash-lite-latest`) and version each prompt.

## 5. Limitations

- Hand reading covers 22 of 234 problems. Group sizes in section 3 are lower bounds.
- Themes in group A come from reading the model's notes, some truncated.
- The rule-based sort uses card names and required quantities as they were in the code at run time.
- One parser model, one batch, one run. The symbolic stratum (687 problems, 90 sampled) is not covered.
- "Near miss" does not mean fixable: a problem one quantity short may still need a second card or a sign rule.
