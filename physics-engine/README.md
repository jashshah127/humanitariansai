# Grade mode: how to apply

Run everything from the git root: `C:\Users\athar\PycharmProjects\humanitariansai`.
Unzip this folder to `C:\Users\athar\Downloads\grade-mode` (adjust paths if different).

## 0. Before you start
    git status
    git branch --show-current        # must say feature-atharva
Commit or stash anything unfinished first. These patches were made against the copies
in the Claude Project; if your local files differ, `--check` below will say so.

## 1. Engine (grade fixes + /parse)
    git apply --check C:\Users\athar\Downloads\grade-mode\patches\1-engine-grade-parse.patch
    git apply C:\Users\athar\Downloads\grade-mode\patches\1-engine-grade-parse.patch
    python physics-engine/eval/ci_check.py       # expect 12 checks, all PASS
    git add physics-engine/server.py physics-engine/engine/grade_mode.py physics-engine/eval/ci_check.py
    git commit -m "Grade: /parse endpoint, grade only verified + asked-for quantities, no answer in feedback, safe errors"

## 2. Contract
    git apply C:\Users\athar\Downloads\grade-mode\patches\2-contract.patch
    git add physics-engine/engine/physics_mode_api.json
    git commit -m "Contract: grade_mode (/parse, /grade), reveal rule, LaTeX fields"

## 3. Frontend
    git apply C:\Users\athar\Downloads\grade-mode\patches\3-frontend-grade-ui.patch
    cd physics-engine/frontend
    npm run format
    npm run typecheck
    npm run lint
    npm test
    npm run build
    cd ../..
    git add physics-engine/frontend
    git status                       # check: no node_modules, no .idea
    git commit -m "Grade mode UI: answer boxes from /parse, GradeView, reveal after 2nd wrong try"
    git push

If a patch fails with "does not apply": your local file differs. Copy the matching file
from `files/physics-engine/...` instead, but first run `git diff <file>` to see what
you would overwrite.

## Manual test (server.py + `npm run dev`)
1. /app?mode=grade, "Numbers" example, press "Enter my answers".
   Expect boxes for acceleration (m/s²) and tension (N), and "The engine read: ..."
2. Enter a=1.96, T=47.04 -> "Correct".
3. Enter a=-1.96 -> "a common mistake". No correct value shown.
4. Enter a=3 twice -> correct value appears after the 2nd wrong try.
5. Type "1.96 m/s^2" -> "Enter only the number" message, nothing sent.
6. "Symbols" example -> "can't be graded" card with Unverified badge.
7. Edit the problem text -> boxes disappear, "The problem has changed".
8. Stop server.py, press Check -> error + Try again (dev message names port 8000).
