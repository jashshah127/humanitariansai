# Design Note: Cache for Repeated Problems

**Author:** Harsh Gujarati · **Plan item:** Wk 6, cache for repeated problems (12 h), cache metrics on the status page (4 h), tests for the cache (6 h)
**Status:** Draft v2, 10 November 2026. v1 asked for review before any code. The reviewer was unavailable, so the build order below keeps the change harmless until someone reviews it. · **Reviewer:** Jash Shah (or Atharva, if Jash cannot)

## 1. What is slow and costly today

Every solve sends the problem to the language model (the parser). That call is the slow part (seconds) and the limited part (the parser's default model allows 20 requests a day on the free tier; the Flash-Lite models allow 500). The solving itself is Python and is fast. So the same problem asked twice costs two model calls today.

**Proposal:** remember the parser's reply for a prompt it has already seen, and return it without calling the model again.

## 2. Where it goes

The parser calls the model through one function, `llm(prompt)`, which returns text. The server builds a **fresh model object for every request** (`_llm()` in `server.py`), so the cache is a module-level store that outlives any single request, and `_llm()` returns the model wrapped in `CachingLLM`.

- **Key:** SHA-256 of the model name and the full prompt. The prompt contains the instructions, the glossary and the problem, so changing the prompt, the glossary or the model changes the key and an old reply is never served for a new setup.
- **Value:** the model's reply text. **Lifetime:** 7 days. **Size:** at most 500 entries (least recently used goes first).
- **Not stored:** a failed call, or an empty reply.
- **A cache fault never breaks a solve:** if the cache raises, the model is called and the fault is counted.

## 3. Build order (changed in v2)

1. **Now: in-memory only, off by default.** The code does nothing unless the environment variable `CACHE_ENABLED=1` is set. It is turned on in staging only, which is my own environment.
2. **Later, after a review: Redis.** `RedisCache` is written but optional: it is used only if `REDIS_URL` is set and the `redis` package is installed. I have **not** added `redis` to `requirements.txt` or declared a Render Key Value instance, because those need a decision.
3. **Merge to `main` only after a reviewer has read the pull request.** With the cache off by default, merging does not change the live service until someone sets `CACHE_ENABLED`.

## 4. Changes to the repository

| File | Change |
|---|---|
| `engine/llm_cache.py` (new) | `MemoryCache`, `RedisCache` (optional), `CachingLLM`, counters, `wrap_llm`, `stats_snapshot` |
| `server.py` | 7 lines: import it, `_llm()` wraps the model, `/health` and the start-up message still report the real provider, `/stats` gains a `"cache"` entry |
| `eval/ci_check.py` | one new offline check, "parse cache" (7 sub-checks) |
| `eval/status_page.py` | later: show the cache counts from `/stats` |

`/health` is unchanged, and no new endpoint is added.

## 5. Privacy

The key is a hash of the prompt, which includes the problem text, and the value is the model's reply, which can quote parts of the problem. Student identity is not part of either. The memory store empties when the service restarts and entries expire after 7 days. If real student work is ever sent through, the retention period and the location of a Redis instance need a decision first.

## 6. Tests (all offline, in `ci_check.py`)

1. The same prompt twice makes **one** model call, and both answers are identical.
2. A different prompt is a miss.
3. A failed model call is not stored, and the error reaches the caller.
4. An empty reply is not stored.
5. A cache that raises does not break the answer, and the fault is counted.
6. Memory is bounded and entries expire.
7. Off by default: with no setting, the model is returned unchanged; with `CACHE_ENABLED`, it is wrapped and can be recovered.

An end-to-end check at the parse level (the stub model, the same problem twice) showed 1 model call and 1 hit.

## 7. Known limits

- **The global rate limiter in `server.py` runs before the parser and still counts a cached request** against its budget (8 per minute). Moving the check after the cache lookup is a separate, larger change and is not part of this one.
- Only exact repeats hit. A problem with one extra space is a different prompt.
- The memory store is per service instance, so it empties on restart and is not shared. Redis would fix that.
- The hit rate on real traffic is unknown until it runs. I will report the measured number, not an estimate.

## 8. Questions for the reviewer

1. Is the in-memory, off-by-default version acceptable to merge into `main`?
2. Should Redis (a new Render Key Value instance and a new dependency) be added, and in whose workspace?
3. Is the `"cache"` entry in `/stats` acceptable, and should the status page read it?
