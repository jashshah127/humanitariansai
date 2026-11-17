# Week 06 (2026-11-09 to 2026-11-15): prompt experiments, symbolic scoring, a status page (in progress)

*Written 2026-11-10 during the week, from my work log, the CI run list and my Claude chat. The week is not finished; the held-out runs were done on 10 Nov and their results are included.*

Planned: 32 hours. Meetings attended so far: 1 (Mon 9 Nov). The Thu 12 Nov meeting is still to come. Hours actually worked so far: 32 (my stated weekly hours, as in my mid-term report; not a logged figure).

## 1. What I worked on
- Prompt experiments on the parser: two variants on 85 problems, judged against control runs.
- Status page (a static site) and a scheduled health-check workflow ([PR #10](https://github.com/jashshah127/humanitariansai/pull/10)).
- Ran symbolic batch 2 of the benchmark (250 problems): 1 answered, and none could be scored.
- Installed antlr4 and made the symbolic answer comparison work; measured that 650 of 667 symbolic answers parse.
- Wrote a design note for a cache of repeated problems, for Jash's review.
- Held-out test (10 Nov) of the default prompt and of `v2` on 149 numeric problems that were not in the experiment set: both answered 0 of 149.

## 2. What I tried, and what I expected
- Tried: variant `v1` (decline when a quantity has more than one value) and `v2` (apply sign conventions). Expected (from my plan of action, a week 5 task finished in week 6): prompt improvements aimed at the top failure modes from the taxonomy.
- Tried: antlr4 and the symbolic comparison. Expected (from my plan of action, a week 5 task finished in week 6): the symbolic/LaTeX comparison path, untested since Phase 1, validated.
- Tried: symbolic batch 2. Expected (from my plan of action for week 6): the complete benchmark, numeric and symbolic, at stratified scale.
- Tried: two offline checks that decline when a stated number or a parsed quantity goes unused. Expected: nothing recorded.

## 3. Where it resisted, and what I did next
- The same prompt and code gave different results on different runs (64% to 76% of problems identical), so I compared against several control runs.
- My first verdict on `v2` used controls that predated a merged change. Claude flagged this and I re-ran the comparison against the matching control.
- `v1` fixed one of three target problems and added noise. `v2` gave three reliable new right answers and two reliable new wrong ones. A prompt rule alone is not safe.
- The offline checks would decline 5 of 7 wrong problems and no right ones, but both were designed after seeing the data, so that is not yet evidence. On the held-out problems the engine answered nothing with either prompt, so the checks could not be tested there. The problems `v2` changed turned out to be the ones the experiment set was built around. One later out-of-sample case helped a little: on the only wrong answer in the symbolic batch, the parsed-but-unused check flagged two quantities, as Claude had predicted before I ran it. One case does not make evidence.
- The LaTeX comparison passed 8 of 15 test pairs, then 12, then 14, then 16 of 16: pi was read as a letter, subscripts were named differently, text answers were read as letters, `g(m_2-m_1)` was read as a function call, and `I` became the imaginary unit. Claude's stand-in test had hidden two of these.
- GitHub's schedule ran the health check only twice in 18 hours; it is a background check, not a guarantee.
- I stayed on a side branch after a merge and put new files on the wrong branch; restored and switched back.
- Copying the key from the editor kept pasting my own command (44 characters, not 53). I loaded it from the project settings instead, checking only length and the last four characters.

## 4. What Claude or another person contributed (accepted, changed, rejected)
- Claude wrote the experiment scripts, comparison tools, the status page, the matcher patches, the workflow and the design note. I ran each against real files; several of Claude's predictions were wrong (a predicted 14 of 15 came out as 12).
- Claude recommended not running the two remaining symbolic batches (1 answered in 250 so far) and testing on held-out problems instead; I did not run them and went on to the held-out run.
- Nothing else recorded as rejected or changed.

## 5. What I understand now, and what I still don't
- Understand now: a result that looks good on the problems I tuned it on is not evidence, and a held-out run is, but only if the engine answers some of those problems. Here it answered none, so the test was inconclusive and says nothing for or against the checks.
- Still unsure: whether the offline checks work on new problems, because the held-out test gave no wrong answers to catch; whether Jash accepts the cache design; Shailly's pull request #9 is not tested or merged.

## Evidence
- [bdf0254](https://github.com/jashshah127/humanitariansai/commit/bdf0254)
- [088868f](https://github.com/jashshah127/humanitariansai/commit/088868f) (methodology)
- [727788a](https://github.com/jashshah127/humanitariansai/commit/727788a)
- [f628ae9](https://github.com/jashshah127/humanitariansai/commit/f628ae9)
- [0eb583f](https://github.com/jashshah127/humanitariansai/commit/0eb583f)
- [PR #10](https://github.com/jashshah127/humanitariansai/pull/10)
- [prompt-methodology.md](https://github.com/jashshah127/humanitariansai/blob/feature-harsh/physics-engine/docs/prompt-methodology.md)
- Status page: https://physics-engine-status.onrender.com/
- Cache design note, in this folder: `cache-design.md`

---

## Update written 2026-11-16 (later than the week it describes; the entry above is unchanged)

**1. What I worked on:** the parse cache, on 10 Nov. An optional cache so a repeated problem skips the model call. Off by default, switched on in staging only. Cache counts added to the status page. Nine offline checks inside `ci_check.py`. The design note in this folder, `cache-design.md`, was updated to a second version once I knew what Jash's absence meant for the order of work.

**2. What I tried, and what I expected:** a cache on staging. Expected (from my plan of action for week 6): a cache for repeated problems, hit and miss counts on the status page, and tests for the cache.

**3. Where it resisted, and what I did next:**
- My first patch to wire the cache into `server.py` put the new function in the middle of the old `_llm()`, because the copy of the file I had tested it on was shorter than the one in my branch. All checks still passed, because none of them called that function with a key set. My own read of the diff caught it before anything was committed. I fixed the patch and added a check that fails when the wrapper is misplaced.
- That new check first failed with "No module named server", because `server.py` sits one folder above where `ci_check.py` looks. I fixed the path inside the check.
- On staging, three solves of one problem made one model call (2 hits, 1 miss, 0 errors). The counters go back to zero when staging redeploys, because the store is in memory.
- I did not build Redis: it needs a new Render service and a new dependency, which need a decision.

**4. What Claude or another person contributed:** Claude wrote the cache module, the patch script and the new check. I applied them, read each diff, ran every check, and tested on staging. I asked whether Jash's review was compulsory since he was unavailable. Claude suggested building it off by default, testing on staging, and holding the merge to `main` for a reviewer. I accepted that.

**5. What I understand now, and what I still don't:**
- Understand now: a patch can pass every test and still be wrong if no test runs the changed code, so reading the diff is part of the work.
- Still unsure: whether the team will accept the cache; Redis is not built; the server's global rate limit still counts a cached request.

**Evidence:** [3e646a6](https://github.com/jashshah127/humanitariansai/commit/3e646a6) (the cache, on `feature-harsh`); the status page https://physics-engine-status.onrender.com/ (staging card shows the cache line); `cache-design.md` in this folder.
