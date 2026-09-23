# Deploy

The service has **zero dependencies beyond what the engine already needs** — no FastAPI, no
uvicorn. It uses Python's standard-library HTTP server, so there is nothing to install
before it runs.

## Run locally (30 seconds)

```bash
export GEMINI_API_KEY=...        # free, no card: aistudio.google.com/apikey
export JWT_SECRET=...             # required -- /solve and /grade are token-gated
python3 server.py
```

Mint a token (separate step, run once, reuse until it expires):
```bash
python3 mint_token.py --sub yourname --hours 24
```

Open **http://localhost:8000**, paste the token into the "Bearer token" field, then type a
problem and get an answer with its verification badge.

Three examples are built into the page — a numeric problem, a symbolic one, and one
deliberately outside the formula library so you can see it decline rather than guess.

## Live deploy

**https://physics-engine-2inp.onrender.com**

Free tier — sleeps after 15 min idle, ~30s to wake on first request after that. Fine for a
demo link, not fine for anything a student depends on being instantly available.

Ask whoever deployed this for a bearer token; there is no self-serve signup (see Auth below
for why).

## Put it on the internet (free)

**Render** — `render.yaml` is included, so it is a Blueprint deploy:
1. render.com → New → Blueprint → select this repo
2. Blueprint Path: `physics-engine/render.yaml` (repo root also holds an unrelated video
   project, so the Blueprint file isn't at the repo root)
3. Add `GEMINI_API_KEY` and `JWT_SECRET` as environment variables in the dashboard
4. Deploy

**Railway / Fly** — same idea, no config file needed:
- build: `pip install -r requirements.txt`
- start: `python3 server.py`
- env: `GEMINI_API_KEY`, `JWT_SECRET`

The server reads `PORT` from the environment, which is what all three platforms set.

## Endpoints

| | |
|---|---|
| `GET /` | Browser UI |
| `GET /health` | Status, card count, active parser |
| `GET /cards` | Everything the engine can solve — worth reading before assuming a decline is a bug |
| `GET /stats` | Route split, latency, coverage gaps this session |
| `POST /solve` | Requires `Authorization: Bearer <token>`. `{"query": "...", "render": "solve"\|"tutor"}` |
| `POST /grade` | Requires `Authorization: Bearer <token>`. `{"query": "...", "student_answer": {"a": 1.96}}` |

## Auth

`/solve` and `/grade` require `Authorization: Bearer <token>` (JWT, HS256, stdlib-only —
see `engine/jwt_auth.py`). `/health`, `/cards`, `/stats` stay open since they leak nothing
sensitive.

Mint a token:
```bash
export JWT_SECRET=...          # must match the value set on the server
python3 mint_token.py --sub yourname --hours 24
```

There is **no token-issuing endpoint**, deliberately — an endpoint that hands out valid
credentials is itself an attack surface, and there's no user database yet to gate one
against. Minting is a manual, offline step someone with `JWT_SECRET` runs, not something
the deployment exposes. If self-serve signup is ever needed, that's a real feature to scope
separately, not an extension of this.

A leaked token is valid until it expires, with no per-user revocation — there's no user
identity behind it yet, just proof someone was handed one. Fine for the current scope; a
reason not to treat this as ready for anything with real stakes riding on who's asking.

## Rate limiting

A global token bucket (`engine/rate_limit.py`) caps `/solve` and `/grade` combined at 8
requests/minute, burst 8 — protecting the one shared Gemini free-tier key from quota
exhaustion. **Global, not per-user**: the quota is shared, so the limit is too. Over the
limit returns `429` with a `Retry-After` header.

This exists because `GeminiLLM`'s own built-in pacing (`self._last`, meant to space out
calls) never actually activates in this server: `_llm()` constructs a fresh `GeminiLLM`
instance per request, so that pacing state never persists across requests. The rate
limiter here is the thing actually protecting the quota, not that class's docstring claim.

## What this is and is not

**Is:** a working demo, gated behind a token, that whoever has one can try — including
breaking it.

**Is not:** a student-facing deployment with real user accounts. Auth proves someone has a
token, not who they are, and nothing is stored server-side. **No student-identified data
should go through this** until Q6 (data processing agreement / IRB) is answered — that
question is about data governance, not access control, and adding auth doesn't answer it.

Free tiers also sleep when idle and take ~30 seconds to wake. Fine for a link you send to
two professors; not fine for a class.

## Known behaviour that looks like a bug and isn't

The engine declines problems outside its 31 formula cards, showing **Unverified**. That is
correct — it refuses to guess. `GET /cards` lists what it does cover. Coverage is the real
constraint, and it is measured in `COVERAGE.md` and `MEASUREMENT.md` rather than hidden.