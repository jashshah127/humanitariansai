# Infrastructure-as-Code Research: 3-Service Deployment

**Author:** Harsh Gujarathi · **Date:** Oct 19, 2026 · **Plan item:** Wk 1, Research (Terraform)
**Status:** Draft, updated Oct 26 with findings from `feature-atharva` (which contains Shailly's backend work) and from the first staging build. Items marked **[verify]** were not confirmed and should be checked before Week 2 work starts. Neither feature branch is merged into `main` yet.

## 1. Services to deploy

| Service | Owner | Current deployment | Source |
|---|---|---|---|
| Engine API (`server.py`, Python, stdlib HTTP server) | Jash / platform | One Render web service, free plan, defined by a Blueprint (`physics-engine/render.yaml`). Live at `physics-engine-2inp.onrender.com` | `render.yaml`, `DEPLOY.md` |
| Frontend (Vite, React, TypeScript) | Atharva | Not a separate service. `server.py` serves the committed `frontend/dist/`. Render does not build the frontend. Sign-in pages and a Supabase client are on `feature-atharva` | CI workflow comment, `server.py`, `src/api/supabase.ts` |
| Backend (Supabase) | Shailly | On `feature-atharva` / `feature-shailly`, not in `main`: `engine/supabase_auth.py`, `server.py` changes, and `supabase/` with `config.toml` and two migrations (initial schema, problems log). She reports it is not live on the online Supabase yet | `git diff --stat`, Shailly's update |

## 2. How the engine is configured today

- **Env vars today (`main`):** `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY`), `JWT_SECRET`, `PORT` (injected by Render).
- **Env vars once the feature branch merges:** add `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` (runtime, read by `server.py`). The frontend also reads `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` **at build time**.
- **Auth after the merge:** `/solve`, `/parse` and `/grade` accept either a Supabase session token or an operator-minted token. Every Supabase request asks Supabase whether the session still exists, so Supabase becomes a runtime dependency of the engine. Minted tokens keep working, so the smoke test design below still applies.
- `render.yaml` declares only `GEMINI_API_KEY` (`sync: false`). `JWT_SECRET` is added by hand in the Render dashboard (`DEPLOY.md`) and is not declared in code.
- `render.yaml` has no `healthCheckPath`, although `/health` exists.
- **A missing secret does not stop the server.** `server.py` prints a warning and keeps running:
  - Missing `JWT_SECRET`: `/health` returns OK, while every `/solve`, `/parse` and `/grade` call returns 401.
  - Missing API key: the parser silently falls back to Ollama, which does not exist on Render, so parsing fails.
- **Rate limit:** a global bucket of 8 requests per minute across `/solve` and `/grade`, shared by all callers.
- **Free tier:** sleeps after 15 minutes idle, about 30s to wake.

## 3. Provider findings

| Provider | What it manages | Notes |
|---|---|---|
| **Render** (official, `render-oss/render`) | Render services such as `render_web_service`, with branch, auto-deploy, build command and repo settings | Render itself recommends Blueprints when no non-Render infrastructure is involved, and the provider when Render must be managed alongside other infrastructure. Launched in early access in May 2024 with possible breaking changes **[verify current maturity on the registry]** |
| **Supabase** (official, `supabase/supabase`) | Resources `supabase_project`, `supabase_settings`, `supabase_branch`. Authenticates with an access token. Existing projects can be imported into state. Settings updates are partial | Table schemas and migrations are most likely handled by the Supabase CLI, not Terraform **[verify]** |
| **GitHub** (`integrations/github`) | Branch protection, Actions secrets, repository settings | Would close the Task 4 gap (checks not enforced on `main`) **[verify resource coverage]** |

## 4. Recommendation

1. **Keep the Render Blueprint for the engine.** It already is infrastructure-as-code for Render. Replacing it with Terraform adds work and early-access risk without adding capability. Improve it: declare `JWT_SECRET` (`sync: false`) and add `healthCheckPath: /health`.
2. **Use Terraform for what the Blueprint cannot do:**
   - Supabase: import Shailly's existing project into state, then manage its settings and a staging branch or project.
   - GitHub: branch protection on `main` requiring the two CI checks, and Actions secrets used by the deploy pipeline.
3. **Revisit moving Render under Terraform** only if the team wants one tool and one state for everything, or if staging and production need to differ in ways a Blueprint cannot express.

## 5. Design decisions

- **State:** remote, never local. Three people on one repo will lose or conflict local state. Options are a cloud storage bucket (GCS or S3) with versioning, or HCP Terraform. **[verify free-tier terms]**
- **Secrets:** never in `.tf` files or committed `tfvars`. Pass the Render API key, the Supabase access token, `GEMINI_API_KEY` and `JWT_SECRET` as sensitive variables from GitHub Actions secrets. State can still contain secret values, so the state backend needs restricted access.
- **Environments:** separate directories (`infra/staging`, `infra/production`) with their own variables, rather than workspaces, so a staging change cannot touch production by accident. Staging gets its own Render service, its own `JWT_SECRET`, and its own Supabase project or branch.
- **Cost:** a second Render service on the free plan was accepted (staging created at $0/month). Render's docs confirm that the 750 free instance hours per month are shared by every free service in the workspace and that spun-down services do not consume them. Free instance hours used so far this month have not been checked. Supabase free-tier limits for a second project or branching **[verify]**.

## 6. Risks to design around

1. **A healthy `/health` does not mean a working deploy.** The pipeline must run an authenticated smoke test: mint a token with `mint_token.py` using the environment's `JWT_SECRET`, call `/solve`, and require a 200. It should also assert that `/health` reports `GeminiLLM` as the provider, which catches a missing API key.
2. **Monitoring (Wk 3)** must track the error rate on `/solve`, not only uptime, for the same reason.
3. **Free-tier sleep** looks like downtime to uptime checks, and keep-alive pings would hide it. Decide which behavior is wanted.
4. **The 8 requests per minute global limit** caps end-to-end tests and the Wk 7 load test. The load test needs a higher limit on staging or a stub parser.
5. **Committed `dist/`:** it goes live as committed, so a frontend change that is not rebuilt and committed does not ship. The CI step that detects this is currently non-blocking.
6. **No token-issuing endpoint by design.** The login Shailly builds in Wk 4 must connect to the engine's own HS256 tokens or replace them. This decision affects auth in the pipeline.

7. **The frontend build bakes in the Supabase project.** `src/api/supabase.ts` reads `import.meta.env.VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`, which Vite substitutes at build time. A single committed `dist/` can therefore point at only one Supabase project. If it was built against production, staging would sign users in against production data. If built with no values, `supabase` is `null` and the app reports that sign-in is not set up. The CD pipeline must build the frontend once per environment with that environment's values, so `dist/` cannot stay a committed artifact for deployment. The CI build runs without these values, so it validates the code but does not produce a deployable build.
8. **Render does not build the frontend today.** Building it per environment can be done in a Render build step: the first staging build ran `npm ci` and `npm run build` on Render's Python runtime and the Vite build finished in 8.79 s, so Node is available on the free plan. The alternative is deploying the frontend as its own static site per environment **[verify free-tier terms]**. Splitting it out also fixes the deep-link 404 (`/app/history`) with a rewrite rule instead of a server change. This is a decision for Atharva and Jash.
9. **Supabase Auth redirect URLs are per environment.** The frontend handles password-reset and email-confirmation links (`arrivedFromRecoveryLink`, `linkError`). Each environment's URL must be on the Supabase allowed-redirect list, or those emails fail on staging **[verify in `config.toml` and the dashboard]**.
10. **The publishable key is public by design, so access control rests on Row Level Security.** Check that both migrations enable RLS on every table, and that the problems-log table cannot be read by ordinary users. Shailly's update says it stores problems without saving who asked, and that should be verified in the SQL **[verify]**.
11. **Migrations need a pipeline step.** Schema lives in `supabase/migrations/` (Supabase CLI layout). Terraform should manage project settings only, and the pipeline needs a step that applies migrations to staging before the engine deploys **[verify the exact CLI command]**. Staging also needs its own Supabase project or branch, which does not exist yet because the online Supabase is not set up.
12. **Free instance hours limit monitoring.** Two free services kept awake by frequent pings use up the 750 monthly hours in about 15 days, and Render then suspends all free services. Monitoring should check infrequently and cover one service, or the demo service should move to a paid instance.
13. **A CI gate needs a check on every commit it guards.** Render's After CI Checks Pass does not deploy a commit with zero checks. The workflow ran only on pull requests, so it needed a `push` trigger for each tracked branch. Done for `feature-harsh`; PR #7 does it for `main`.

## 7. Open questions

For the manager:
- Stay on Render for production, or move?
- Who owns the Render account, the Supabase org and the GitHub admin settings for the pipeline?

For the team:
- **Shailly:** Supabase project ref and org ID once the online project exists, and a date for that. Answered by the repo: migrations are in `supabase/migrations/`, auth is token-based, and minted tokens still work alongside Supabase tokens. Her Wk1 plan has not been received.
- **Atharva / Jash:** should the frontend deploy as its own static site, built per environment? His branch still commits `dist/`, which conflicts with per-environment builds. When will `feature-atharva` merge, and in what order relative to Shailly's work?
- **Render (answered):** the existing `physics-engine` service tracks `main`, is Blueprint-managed, has Auto-Deploy On Commit, and had no health check path. Auto-Deploy does offer After CI Checks Pass, and it is proven on staging (good commit deployed, failing commit not deployed, revert deployed).

## 8. Next steps (Week 2)

1. Add `JWT_SECRET`, the Supabase variables and `healthCheckPath` to `render.yaml` (Supabase variables once the branch merges).
2. CD gate: done for staging (After CI Checks Pass, tested on three commits). Still to add: the authenticated smoke test, and the same gate for the `main`-tracking service once PR #7 merges.
3. Staging is up and verified. Its infrastructure-as-code is written and validated (`physics-engine/infra/staging/render.yaml` with a recreation README) but not applied, so Render does not manage the service yet.
