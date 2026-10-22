"""
SUPABASE AUTH -- checks that a bearer token belongs to a signed-in Supabase user.

Standard library only, for the same reason as jwt_auth.py: server.py must run with
nothing to install beyond the engine's own requirements.

HOW IT CHECKS: it asks Supabase. The token goes to GET <SUPABASE_URL>/auth/v1/user; a 200
means the session is live and returns the user. That was chosen over verifying the
signature locally (cached JWKS + ES256) for three reasons, all tested against a real
project:
  * stdlib has no ES256 support -- local verification would need PyJWT + cryptography;
  * sign-out takes effect at once: after /auth/v1/logout this endpoint answers
    403 session_not_found, while a locally-verified token stays valid until it expires
    (up to 60 minutes);
  * it does not care how tokens are signed. The hosted project signs with ES256, the
    local CLI stack with HS256 -- one code path covers both.
The cost is one network round-trip per request. If that ever matters, switch to local
verification here; callers only see verify_supabase_token().

TWO DIFFERENT FAILURES, deliberately two exception types:
  * TokenError      -- Supabase looked at the token and refused it (expired, signed out,
                       forged). The caller should answer 401.
  * AuthUnavailable -- Supabase could not be asked (not configured, timeout, outage). The
                       caller should answer 503. Answering 401 here would tell a signed-in
                       user their session is bad when the problem is ours.
"""
import json
import os
import urllib.error
import urllib.request

from jwt_auth import TokenError

TIMEOUT_S = 5


class AuthUnavailable(Exception):
    """Supabase Auth could not be reached or is not configured -- not the caller's fault."""


def configured():
    """True when the server has been told which Supabase project to trust."""
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_PUBLISHABLE_KEY"))


def _urllib_fetch(url, headers, timeout):
    """Default transport. Returns (status, body_bytes); never raises on an HTTP error code."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def verify_supabase_token(token, fetch=None):
    """Returns the Supabase user for `token` as {"id", "email"}. Raises TokenError if
    Supabase rejects it, AuthUnavailable if Supabase can't be asked.

    fetch: callable(url, headers, timeout) -> (status, body_bytes). Injected by tests so
    they run with no network; defaults to urllib."""
    if not configured():
        raise AuthUnavailable("SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY not set")
    url = os.environ["SUPABASE_URL"].rstrip("/") + "/auth/v1/user"
    headers = {"apikey": os.environ["SUPABASE_PUBLISHABLE_KEY"],
               "Authorization": f"Bearer {token}"}
    try:
        status, body = (fetch or _urllib_fetch)(url, headers, TIMEOUT_S)
    except (TimeoutError, urllib.error.URLError, ConnectionError, OSError) as e:
        raise AuthUnavailable(f"could not reach Supabase Auth: {type(e).__name__}")

    if status == 200:
        try:
            user = json.loads(body)
            return {"id": user["id"], "email": user.get("email")}
        except (ValueError, KeyError, TypeError):
            raise AuthUnavailable("unexpected response from Supabase Auth")
    if status in (401, 403):
        # 403 session_not_found = signed out; 401/403 bad_jwt = expired or forged.
        raise TokenError("Supabase session is not valid (expired or signed out)")
    raise AuthUnavailable(f"Supabase Auth answered {status}")
