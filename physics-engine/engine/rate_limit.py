"""
RATE LIMIT -- a global token bucket protecting the shared Gemini free-tier quota.

Deliberately GLOBAL, not per-IP or per-user: the thing being protected is one shared
API key's quota, which every caller draws from together. A per-IP limiter would let
two people each stay "under their own limit" while jointly exhausting the same quota
-- the failure mode this exists to prevent. If per-user fairness is ever needed on top
of this, add it as a second, separate layer; don't fold it into this one.

Token bucket over fixed-window because it tolerates a small burst (someone testing
three problems in a row) without the "reset boundary" unfairness of a fixed window,
where 2x the limit can slip through right at a minute boundary.

Threading.Lock because server.py uses ThreadingHTTPServer -- concurrent requests
genuinely happen, and an unlocked read-modify-write on the token count would let two
simultaneous requests both read "1 token available" and both proceed, silently
doubling the effective limit under load. That race is easy to miss in testing (which
tends to be sequential) and easy to hit in production (which isn't).
"""
import threading
import time


class RateLimiter:
    def __init__(self, rate_per_minute, burst=None):
        """rate_per_minute: sustained requests allowed per minute, long-run.
        burst: max requests allowed in a sudden spike (bucket capacity). Defaults to
        rate_per_minute if not given -- i.e. no extra burst allowance beyond one
        minute's worth banked up."""
        self.rate = rate_per_minute / 60.0  # tokens refilled per second
        self.capacity = burst if burst is not None else rate_per_minute
        self.tokens = float(self.capacity)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def allow(self):
        """Returns (True, 0) if the request may proceed, consuming one token.
        Returns (False, retry_after_seconds) if not -- caller should reject with 429
        and that Retry-After value, not just "no"."""
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True, 0
            wait = (1 - self.tokens) / self.rate
            return False, wait