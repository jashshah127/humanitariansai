# Deploy

The service has **zero dependencies beyond what the engine already needs** — no FastAPI, no
uvicorn. It uses Python's standard-library HTTP server, so there is nothing to install
before it runs.

## Run locally (30 seconds)

```bash
export GEMINI_API_KEY=...        # free, no card: aistudio.google.com/apikey
python3 server.py
```

Open **http://localhost:8000**. Type a problem, get an answer with its verification badge.

Three examples are built into the page — a numeric problem, a symbolic one, and one
deliberately outside the formula library so you can see it decline rather than guess.

## Put it on the internet (free)

**Render** — `render.yaml` is included, so it is a Blueprint deploy:
1. render.com → New → Blueprint → select this repo
2. Add `GEMINI_API_KEY` as an environment variable in the dashboard
3. Deploy

**Railway / Fly** — same idea, no config file needed:
- build: `pip install -r requirements.txt`
- start: `python3 server.py`
- env: `GEMINI_API_KEY`

The server reads `PORT` from the environment, which is what all three platforms set.

## Endpoints

| | |
|---|---|
| `GET /` | Browser UI |
| `GET /health` | Status, card count, active parser |
| `GET /cards` | Everything the engine can solve — worth reading before assuming a decline is a bug |
| `GET /stats` | Route split, latency, coverage gaps this session |
| `POST /solve` | `{"query": "...", "render": "solve"\|"tutor"}` |
| `POST /grade` | `{"query": "...", "student_answer": {"a": 1.96}}` |

## What this is and is not

**Is:** a working demo anyone can open in a browser and try, including breaking it.

**Is not:** a student-facing deployment. There is no authentication, and nothing is stored.
Both are deliberate — but it means **no student-identified data should go through this**
until Q6 (data processing agreement / IRB) is answered.

Free tiers also sleep when idle and take ~30 seconds to wake. Fine for a link you send to
two professors; not fine for a class.

## Known behaviour that looks like a bug and isn't

The engine declines problems outside its 31 formula cards, showing **Unverified**. That is
correct — it refuses to guess. `GET /cards` lists what it does cover. Coverage is the real
constraint, and it is measured in `COVERAGE.md` and `MEASUREMENT.md` rather than hidden.
