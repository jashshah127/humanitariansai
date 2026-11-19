"""
A cache for the parser's model calls. Off unless CACHE_ENABLED is set.

The parser sends one prompt to a language model and gets text back. The prompt holds the
instructions, the glossary and the problem, so the same prompt always asks the same question.
This wrapper remembers the reply and returns it the next time, without calling the model.

  - Key: SHA-256 of the model name and the full prompt. Change the prompt, the glossary or the
    model and the key changes, so an old reply is never served for a new setup.
  - Only successful, non-empty replies are stored. A failed call is never remembered.
  - A cache fault never breaks a solve: if the cache raises, the call goes to the model and
    the fault is counted.
  - Storage: in memory (default, bounded, with a lifetime). Redis is used only if REDIS_URL is
    set AND the redis package is installed; otherwise it falls back to memory.

Settings (environment variables):
    CACHE_ENABLED         "1" or "true" to turn the cache on (default off)
    CACHE_MAX_ENTRIES     memory limit, default 500
    CACHE_TTL_SECONDS     lifetime of an entry, default 604800 (7 days)
    REDIS_URL             optional, e.g. a Render Key Value internal URL
"""
import hashlib
import os
import threading
import time
from collections import OrderedDict


class CacheStats:
    def __init__(self):
        self._lock = threading.Lock()
        self.hits = self.misses = self.errors = self.stores = 0

    def add(self, name):
        with self._lock:
            setattr(self, name, getattr(self, name) + 1)

    def snapshot(self):
        with self._lock:
            total = self.hits + self.misses
            return {"hits": self.hits, "misses": self.misses, "errors": self.errors,
                    "stores": self.stores, "hit_rate": round(self.hits / total, 3) if total else None}


class MemoryCache:
    """Least recently used, bounded, with a lifetime per entry."""

    def __init__(self, max_entries=500, ttl_seconds=7 * 24 * 3600, clock=time.time):
        self.max_entries, self.ttl, self.clock = max_entries, ttl_seconds, clock
        self._data = OrderedDict()
        self._lock = threading.Lock()
        self.name = "memory"

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            value, expires = item
            if expires < self.clock():
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return value

    def set(self, key, value):
        with self._lock:
            self._data[key] = (value, self.clock() + self.ttl)
            self._data.move_to_end(key)
            while len(self._data) > self.max_entries:
                self._data.popitem(last=False)

    def __len__(self):
        with self._lock:
            return len(self._data)


class RedisCache:
    def __init__(self, url, ttl_seconds):
        import redis  # raises ImportError if the package is not installed
        self._r = redis.Redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
        self.ttl = ttl_seconds
        self.name = "redis"

    def get(self, key):
        v = self._r.get("llmcache:" + key)
        return v.decode("utf-8") if v is not None else None

    def set(self, key, value):
        self._r.set("llmcache:" + key, value, ex=self.ttl)

    def __len__(self):
        return -1  # not tracked for Redis


def _model_tag(llm):
    """A string naming the model (or chain of models) behind llm, so a change of model changes
    the cache key. Set CACHE_VERSION to throw away every old entry by hand."""
    parts, seen = [], set()

    def walk(o, depth):
        if o is None or id(o) in seen or depth > 3:
            return
        seen.add(id(o))
        m = getattr(o, "model", None)
        parts.append(type(o).__name__ + (":" + m if isinstance(m, str) else ""))
        for v in getattr(o, "__dict__", {}).values():
            if isinstance(v, (list, tuple)):
                for x in v:
                    if callable(x) and not isinstance(x, (str, bytes)):
                        walk(x, depth + 1)

    walk(llm, 0)
    return "|".join(parts) + "|v" + os.environ.get("CACHE_VERSION", "1")


class CachingLLM:
    """Same call signature as the model classes: llm(prompt) -> text."""

    def __init__(self, inner, cache, stats):
        self.inner, self.cache, self.stats = inner, cache, stats
        self.model = _model_tag(inner)

    def _key(self, prompt):
        return hashlib.sha256((self.model + "\n" + prompt).encode("utf-8")).hexdigest()

    def __call__(self, prompt):
        key = self._key(prompt)
        try:
            cached = self.cache.get(key)
        except Exception:  # noqa: BLE001 - a cache fault must never break a solve
            self.stats.add("errors")
            cached = None
        if cached is not None:
            self.stats.add("hits")
            return cached
        self.stats.add("misses")
        reply = self.inner(prompt)  # an exception here propagates and nothing is stored
        if isinstance(reply, str) and reply.strip():
            try:
                self.cache.set(key, reply)
                self.stats.add("stores")
            except Exception:  # noqa: BLE001
                self.stats.add("errors")
        return reply


_STATE = {"cache": None, "stats": None, "built": False}
_STATE_LOCK = threading.Lock()


def _enabled():
    return os.environ.get("CACHE_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


def _build():
    ttl = int(os.environ.get("CACHE_TTL_SECONDS", 7 * 24 * 3600))
    url = os.environ.get("REDIS_URL", "").strip()
    cache = None
    if url:
        try:
            cache = RedisCache(url, ttl)
        except Exception:  # noqa: BLE001 - package missing or bad URL: fall back to memory
            cache = None
    if cache is None:
        cache = MemoryCache(int(os.environ.get("CACHE_MAX_ENTRIES", 500)), ttl)
    return cache, CacheStats()


def wrap_llm(llm):
    """Return the model unchanged when the cache is off, a caching wrapper when it is on."""
    if not _enabled():
        return llm
    with _STATE_LOCK:
        if not _STATE["built"]:
            _STATE["cache"], _STATE["stats"] = _build()
            _STATE["built"] = True
    return CachingLLM(llm, _STATE["cache"], _STATE["stats"])


def unwrap(llm):
    return getattr(llm, "inner", llm)


def stats_snapshot():
    if not _enabled() or not _STATE["built"]:
        return {"enabled": _enabled(), "backend": "off" if not _enabled() else "not used yet"}
    out = {"enabled": True, "backend": _STATE["cache"].name, "entries": len(_STATE["cache"])}
    out.update(_STATE["stats"].snapshot())
    return out


def _reset_for_tests():
    with _STATE_LOCK:
        _STATE.update(cache=None, stats=None, built=False)
