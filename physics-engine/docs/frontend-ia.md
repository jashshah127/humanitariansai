# Physics Engine Frontend: Page and Component Plan

**Owner:** Atharva · **Week 1 deliverable** · **Status:** Draft for the Thursday Oct 8 meeting

This plan is based on the code that exists today (`App.jsx`, `Result.jsx`, `api.js`, `main.jsx`, `styles.css`), the API contract (`physics_mode_api.json`), and the routes in `server.py`.

---

## 1. Design rules taken from the API contract

These rules shape the whole layout. Every screen must follow them.

1. **The verification badge is the most important thing on the screen. The answer comes second.** The contract says that dropping the badge "removes the reason this mode exists."
2. **Never show an answer under a "Verified" badge unless the server said `verified`.** If the state is missing or unknown, treat it as `unverified`.
3. **For `needs_review`, show every candidate.** Never pick one for the student.
4. **Hints are shown one at a time, and the answer comes last.**
5. **Never show `route` or `trace` to students.** They exist only for debugging.
6. **The mode choice belongs next to the input box. It is not a separate page.** The contract compares it to Google's AI Mode toggle. Solve, Hints, and Grade are three views of the same problem, so they share one screen.

---

## 2. Pages and routes

| Route | Page | Who can see it | Plan week | Depends on |
|---|---|---|---|---|
| `/` | Landing page | Public | Wk 7 | — |
| `/app` | **Workspace** (input, mode toggle, result) | Logged in (from Wk 4) | Wk 1–3 | — |
| `/app?mode=solve\|tutor\|grade` | Same page with a mode already picked | Logged in | Wk 2–3 | — |
| `/app/history` | Problem history list with search and filter | Logged in | Wk 6 | Shailly's stored history |
| `/app/history/:id` | One past problem, reopened in the workspace | Logged in | Wk 6 | Shailly's stored history |
| `/login`, `/signup` | Login and signup | Public | Wk 4 | Shailly's login |
| `/coverage` | "What can this engine solve?" (from `GET /cards`) | Public | *Not in plan, proposed* | — |
| `/help` | Help and FAQ | Public | Wk 10 | — |
| `*` | Not-found page | Public | Wk 5 | — |

**Why the workspace lives at `/app` from day one:** the landing page will take over `/` in Week 7. If the workspace starts at `/`, its address changes in Week 7, and every link and test that points at it breaks.

**Why the mode goes in the URL:** a teacher can share a link that opens straight into Hints mode, and the end-to-end tests can open a specific mode directly.

**Proposed `/coverage` page:** this page is not in the plan. It is cheap to build because `GET /cards` already exists. It also gives the "out of scope" result somewhere useful to point the student. Its cost would come out of polish time. This needs a manager decision.

---

## 3. Component tree

```
App
├── AppShell                    header, nav, footer, theme
│   ├── NavBar                  logo, Workspace / History / Help, UserMenu
│   └── UserMenu                (Wk 4) shows the logged-in user, logout
│
├── LandingPage                 (Wk 7)
│   ├── Hero
│   ├── HowVerificationWorks    explains the three badge states
│   └── ExamplesShowcase
│
├── WorkspacePage               /app
│   ├── ProblemInput            textarea, Ctrl/Cmd+Enter to submit, character limit
│   ├── ModeToggle              Solve | Hints | Grade (next to the input, per the contract)
│   ├── ExampleChips            example problems (could later come from /cards)
│   ├── StudentAnswerForm       (Grade mode only) one input per unknown, plus optional steps
│   └── ResultPanel             picks a view based on the response
│       ├── VerificationBadge   ALWAYS rendered first, for every response
│       ├── EngineNotice        shown when needs_llm_completion is true
│       ├── SolveView
│       │   ├── AnswerList      variable = value, with units once the backend sends them
│       │   └── MathFormula     KaTeX wrapper (see blocker B1)
│       ├── CandidateList       needs_review: every candidate with its "applies when"
│       ├── HintLadder          tutor mode: one hint at a time, answer last
│       ├── GradeView           assessment, per-quantity check, misconception, feedback
│       ├── WhyPanel            formula used, assumptions, "read from your text" sources
│       ├── Visualization       (Wk 3–4) TrajectoryPlot, AtwoodDiagram (see blocker B2)
│       └── FeedbackButtons     (Wk 10) "Was this helpful?"
│
├── HistoryPage                 (Wk 6)
│   ├── HistoryFilters          topic, verification state, text search
│   ├── HistoryList → HistoryItem
│   └── SimilarProblems         (Wk 6) Shailly's semantic search
│
├── LoginPage / SignupPage      (Wk 4)
├── CoveragePage                (proposed)
├── HelpPage                    (Wk 10)
└── NotFoundPage

Shared UI (design system, Wk 1):
Button · Input · TextArea · Select · Card · Badge · Spinner/Skeleton
ErrorState · EmptyState · Tooltip
```

**Why `VerificationBadge` sits outside the per-mode views:** if every mode view had to remember to render the badge, one of them would eventually forget. With the badge rendered once in `ResultPanel` above all views, there is no code path that shows an answer without it. Add a component test that proves this.

---

## 4. Existing code: keep, change, or replace

| Existing piece | Decision | Reason |
|---|---|---|
| `api.js` — `solve()`, `ApiError`, error handling for 401 / 429 / network | **Keep** (convert to TypeScript) | Already correct against the contract. Needs `grade()` and `cards()` added. |
| `api.js` — `sessionId()` | **Keep** | The contract requires `session_id`. The code already handles blocked storage. |
| `api.js` — `loadToken` / `saveToken` (localStorage) | **Replace in Wk 4** | Will be replaced by Shailly's login. Ask her whether her login uses a cookie or a token, because that changes how `api.ts` sends requests. |
| `App.jsx` — the whole file | **Replace** | Today it is one component holding all the state. It gets split into `WorkspacePage`, `ProblemInput`, `ModeToggle`, and `ExampleChips`. |
| `App.jsx` — token input field | **Delete in Wk 4** | Users paste a token from `mint_token.py`. This is a developer workaround, not a product feature. |
| `App.jsx` — `<select>` for solve/tutor | **Replace** | Becomes `ModeToggle` with three options, including Grade. |
| `App.jsx` — `EXAMPLES` list | **Keep** (move into `ExampleChips`) | Useful as is. Could later come from `/cards`. |
| `App.jsx` — `ErrorBox` | **Keep the logic, restyle** | Becomes `ErrorState`. Keep the "retry in Ns" behavior for rate limits. |
| `App.jsx` — `resultId` key that resets the hint ladder | **Keep the idea** | Without it, a new problem would open with the old problem's hint count. |
| `Result.jsx` — "unknown state → unverified" | **Keep exactly** | This is the contract's main rule. Copy it into `VerificationBadge` along with a test. |
| `Result.jsx` — skipping sources that have no phrase | **Keep exactly** | Stops the page from ever showing `v from "null"`. |
| `Result.jsx` — `fmt()` (5 significant figures) | **Keep** | Move into `utils/format.ts`. |
| `Result.jsx` — `Hints` | **Keep the logic, restyle** | Becomes `HintLadder`. The reveal logic is already correct. |
| `Result.jsx` — candidates, assumptions, and sources blocks | **Keep the logic, split up** | Become `CandidateList` and `WhyPanel`. |
| `Result.jsx` — latency shown to students | **Remove from the student view** | Of no use to a student. Show it only in a dev/debug mode. |
| `styles.css` | **Replace** | Replaced by design tokens (colors, type scale, spacing) in Wk 1. |
| `main.jsx`, `index.html` | **Keep** (rename to `.tsx`) | Add the router here. |
| `vite_config.js` proxy | **Keep** | Already forwards `/solve`, `/grade`, `/cards`, `/stats`, `/health`. Add the auth routes in Wk 4. |
| Inline HTML page in `server.py` (`INDEX`) | **Delete** (backend change, ask your manager) | The code's own comment says to remove it once the React build is live. While it exists, a missing build fails silently. |

**What this means for the plan:** most of the code is kept, and the work is splitting it up and converting it. That is less work than a rebuild from scratch. It saves part of the Week 2 hours ("problem-input UI" and "wire up /solve" are mostly done) and part of the Week 3 hours (the hint ladder logic is done). Use the saved hours as buffer. Do not fill them with new features.

---

## 5. Blockers found while writing this plan

These need backend changes or decisions. None of them is in the current plan.

**B1. KaTeX has nothing to render.** `formula_used` is a plain name (for example, "Atwood machine"), not a math formula. The symbolic forms live inside `trace`, and `server.py` removes `trace` from responses (`d.pop("trace")`). So the Week 2 KaTeX task (8 h) needs the backend to add a field such as `formula_latex`. Without it, KaTeX can only style variable names.

**B2. The visualizations do not have their input numbers.** The trajectory plot needs v₀ and θ. The response only gives `answer` (the unknowns) and `sources` (the text phrases each value came from, not the numbers). The Week 3 and Week 4 visualization tasks (20 h total) need the backend to return the parsed known values (for example, `knowns: {v0: 25, theta: 40}`). The other option is to parse numbers out of the phrases on the frontend, which is fragile.

**B3. Deep links will return 404.** `static_files.resolve()` only serves files that exist in `dist/`. Opening `/app/history` directly or refreshing the page will return `{"error": "not found"}`. There are two fixes:
- **Option A (better):** change `server.py` so that any GET request that is not an API route and not a file returns `index.html`. This is a few lines of backend code.
- **Option B:** use hash URLs (`/#/app/history`). No backend change, but the URLs are uglier and SEO for the landing page is worse.

Decide this before setting up the router in Week 1.

**B4. Grade mode asks for variable names students won't know.** `/grade` expects `student_answer` as a dictionary (`{"a": 1.96, "T": 47.04}`). A student does not know the engine calls tension `T`. The UI needs the list of unknowns before the student answers. There are two options:
- **Option A:** call `/solve` first in a "parse only" step to get the unknowns.
- **Option B:** have the backend return the unknowns in a lighter request.

This decides how `StudentAnswerForm` works.

**B5. The contract file is out of date.** `physics_mode_api.json` says grade mode is "not implemented," but `server.py` has a working `/grade` route. The grade response shape (`assessment`, `per_quantity`, `reference_answer`, `misconception`, `feedback`, `confidence`) only exists in the Python code. Write it into the contract before building `GradeView`, or the frontend will be built against an unwritten spec.

**B6. Units are missing.** Answers come back as plain numbers. A physics answer shown without units looks broken to a student. A `units` field is needed from the backend, or a frontend lookup table per variable.

**B7. Showing the reference answer in grade mode.** `GradeResult` includes `reference_answer`. Should a student who got it wrong see the right answer right away? That is a teaching decision, not a frontend one. Ask about it.

---

## 6. Folder structure (Vite + TypeScript)

```
frontend/
├── src/
│   ├── main.tsx
│   ├── router.tsx
│   ├── api/
│   │   ├── client.ts         fetch wrapper, ApiError, session id
│   │   ├── solve.ts
│   │   ├── grade.ts
│   │   ├── cards.ts
│   │   └── types.ts          response types copied from physics_mode_api.json
│   ├── design/
│   │   ├── tokens.css        colors, type scale, spacing, dark mode
│   │   └── components/       Button, Input, Card, Badge, ...
│   ├── features/
│   │   ├── workspace/        WorkspacePage, ProblemInput, ModeToggle, ...
│   │   ├── result/           ResultPanel, VerificationBadge, HintLadder, ...
│   │   ├── visualization/
│   │   ├── history/          (Wk 6)
│   │   └── auth/             (Wk 4)
│   ├── pages/                Landing, Coverage, Help, NotFound
│   └── utils/format.ts
└── tests/
```

**Write `api/types.ts` first.** If the response types match the contract exactly, TypeScript will flag any component that reads a field that doesn't exist, or that forgets to handle `needs_review`.

---

## 7. Decisions needed at Thursday's meeting

1. Convert the existing code (this plan) or rebuild from scratch?
2. B3: fix deep links with a server fallback (needs a backend change) or use hash URLs?
3. B1, B2, B6: who adds `formula_latex`, `knowns`, and `units` to the response, and by when? The Week 2–4 tasks depend on these fields.
4. B4: how does grade mode get the list of unknowns?
5. B7: does a student see the reference answer after a wrong grade?
6. Is the `/coverage` page in or out?
7. Does Shailly's login use a cookie or a token?