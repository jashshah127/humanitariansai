# Coverage: 16 cards vs. 1,226 real UGPhysics problems

First measurement of the formula-card KB against real external data rather than our own
golden set. Run against `eval/ugphysics_ClassicalMechanics.csv` (836) and
`eval/ugphysics_ClassicalElectromagnetism.csv` (390), pulled Aug 3.

**This is topic-level coverage, which is a generous upper bound, not an accuracy figure.**
It answers "does the KB have any card in this area at all," not "can it solve this
problem." Real accuracy requires parsing all 1,226 through a live model — still blocked on
an API key. Read every number below as a ceiling.

| Topic | Problems | Cards | Ratio |
|---|---|---|---|
| Particle Dynamics | 322 | 6 | 1 : 53 |
| Electrostatics | 184 | 3 | 1 : 61 |
| Rigid-Body Dynamics | 180 | 1 | 1 : 180 |
| **Vibrations and Waves** | **179** | **8** | **1 : 22** (was zero cards) |
| Magstatics | 148 | 3 | 1 : 49 |
| Central Force Motion | 78 | 1 | 1 : 78 |
| Fluid Mechanics | 77 | 0 | out of scope by decision |
| Circuit Analysis | 58 | 2 | 1 : 29 |

- In a topic with at least one card: **970 / 1,226 (79%)** — upper bound
- In a topic with zero cards: **256 / 1,226 (21%)**

## The finding that changed the backlog — now closed

**Vibrations and Waves was 179 problems — the fourth largest topic — with zero cards.**

SHM was locked *into* scope on Aug 3, with the reasoning that UGPhysics would "almost
certainly include SHM problems, so leaving it out would create an immediate coverage gap
against our own crosscheck source." That prediction was right, and the gap measured at 179
problems — 76 of them numerically scorable, the most of any topic.

**Eight cards now cover it**, built directly against real benchmark problems: wave relation,
wave properties from y=A sin(kx-wt), SHM spring period, amplitude combination, critical
damping, Doppler effect, and standing waves in open and closed pipes. Escape velocity was
added alongside, since the KB had orbital velocity only and the two are routinely confused.

Each was checked against actual UGPhysics published answers — wavelength 4 cm and wave speed
60 cm/s from a real benchmark wave equation, amplitude 0.5 from 0.4sin+0.3cos, Moon escape
velocity 2.37 km/s. All match.

**Fluid Mechanics (77) validates the opposite call.** Ruled out of scope the same day; the
data confirms it as a genuinely separate area rather than an oversight.

## What the ratios actually say

One rotation card against 180 Rigid-Body Dynamics problems is not coverage in any
meaningful sense — it is one worked pattern in a large topic. The 79% figure counts a
topic as covered if a single card touches it, so the honest reading is: **the KB has
footholds in six of eight topics and nothing in two.** Depth is the gap, not breadth.

## Next, in order

1. **Build the SHM card** — largest measured gap, already in scope, no scope debate needed.
2. **Run the real parse** (`ClaudeLLM` instead of `StubLLM`) over a sample of these
   problems to convert this ceiling into an actual accuracy number.
3. Use per-problem failures to rank card-building beyond SHM, which is the curate loop
   running on real data instead of examples.
