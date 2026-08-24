# Commercial assessment

Sri asked whether this could sell as an app, and floated it as a potential replacement for
MATLAB and Mathematica. Taking both questions seriously, and answering the second one
first because the answer shapes everything else.

## Is this a MATLAB or Mathematica replacement? No — and the reason matters

Not a matter of maturity or roadmap. Three structural reasons:

**1. We're built on top of the thing that already competes with them.** Every calculation
runs through SymPy, which *is* the open-source alternative to Mathematica's symbolic
engine. We're a thin verification-and-honesty layer on that, not a competitor to it. A
Mathematica replacement would need to replace SymPy, not wrap it.

**2. Different product category.** MATLAB and Mathematica are general-purpose computational
environments — you bring your own problem in any domain and program a solution. We take a
natural-language physics question and return a verified answer from a library of 16 known
patterns. Those aren't the same product at different scales; they're different products.

**3. Scale.** 16 formula cards in intro mechanics and E&M, against decades of development
and tens of thousands of functions. On the measured benchmark, 18% of an undergraduate
physics set is even scorable against us today (see `MEASUREMENT.md`).

**Worth stating plainly because the risk runs one direction.** If "Mathematica replacement"
becomes the internal framing, every subsequent update reads as a shortfall against a target
that was never reachable. The honest framing has a genuinely good story; the inflated one
guarantees disappointment.

## The real competitive set

Not MATLAB. It's the student-facing solver market — and the closest comparison is
**Wolfram Alpha**, which is a serious, entrenched incumbent: <cite index="8-1">it's famous for math and physics, offers step-by-step solutions with hints and intermediate methods, supports photo input for problems, and runs $9.99/month or up to $59.99/year</cite>. Also in the set:
**Photomath** (<cite index="9-1">free with a Pro tier at $9.99/month or $69.99/year, camera-first, strongest handwriting recognition, but mobile-only and limited above high-school level</cite>), **Symbolab**,
**Mathway**, and a wave of AI-native entrants.

Note the pattern: **$10/month is the established price ceiling** in this category, and the
incumbents already do photo input and step-by-step. Those aren't differentiators available
to us — they're table stakes we don't yet have.

## Where there is a real, defensible wedge

One honest gap in the incumbents, and it's ours: **they don't tell you when they're
unreliable.** <cite index="11-1">Accuracy across the top tools is above 95% on common problem types but drops on edge cases, ambiguous word problems, and advanced topics — with the standard advice being to never rely on a single tool without verifying the method yourself, and to cross-check critical problems.</cite>

That advice exists because the tools give no signal about which answers to distrust. A
student can't tell a 99%-confident answer from a 60%-confident one. Our routing does exactly
that, and it's the one thing in this build that isn't a commodity.

Two markets where that's worth real money, and they're different:

**Instructors and institutions (stronger).** A tool that says "verified" or "not verified"
is something a professor can put in front of a class without risking endorsing wrong
answers. Institutional sales are higher-value, stickier, and the honesty property is worth
*more* to a department than to a student. It also fits Medhavy's existing distribution and
the teach loop already in the brief. Grade mode — where reproducibility is a fairness
requirement, not a nice-to-have — has no real equivalent in the consumer tools.

**Direct-to-student (weaker).** Competing head-on with Wolfram Alpha on physics at $10/month
means matching photo input, breadth, and step-by-step, then differentiating on a property
students may not value until it's already burned them. Hard sell, thin margin, entrenched
incumbents.

## Honest verdict

**As a standalone consumer app: not today, and the gap isn't small.** 16 problem patterns
against Wolfram Alpha's coverage isn't a version-one disadvantage, it's a different order of
magnitude. Nothing is deployed, no student has used it, and parse accuracy is still
unmeasured.

**As a differentiating capability inside Medhavy: strong, and the strategic fit is real.**
The verification badge is a genuine wedge, the floor never drops below a normal chatbot
answer, and it's exactly the property an educational institution needs and current tools
don't offer.

**As a licensable component: the most interesting option, and worth deliberate thought.**
Every EdTech company shipping an AI tutor has our problem — their tutor is confidently wrong
sometimes and they can't tell which times. "Verified physics answers as an API" is a
narrower, more defensible pitch than another consumer solver app, and it doesn't require
beating Wolfram Alpha on breadth to be valuable.

## What would need to be true before betting on any of it

1. **Parse accuracy measured.** Everything downstream is conditional on this. Needs an API key.
2. **Coverage past 16 cards.** The symbolic-output change in `MEASUREMENT.md` roughly 4× what's
   measurable and is a prerequisite for a credible coverage claim.
3. **One real classroom.** Zero students have used this. The verification badge is a
   hypothesis about what students value, not a finding.
4. **The data question settled** (Q6 — data processing agreement, IRB). Any commercial path
   involving student data needs this answered first, not in parallel.
