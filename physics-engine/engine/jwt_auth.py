"""
AUTH -- minimal JWT (HS256) issuing and verification, standard library only.

Deliberately not using PyJWT: server.py's whole design point is "nothing to install
before it runs" (see its own docstring). A dependency for this would silently break
that guarantee. HS256 (HMAC-SHA256) is ~40 lines of stdlib code, well-understood, and
sufficient for a single shared-secret setup with no key rotation infrastructure --
which is what this project needs.

NOT implemented, because they are not needed yet and would be speculative complexity:
  * RS256 / asymmetric signing (needed only if a third party must verify tokens
    without holding the signing secret)
  * key rotation / kid header (needed only once there's more than one active secret)
  * refresh tokens (needed only once short-lived access tokens are actually painful)

If any of those become real requirements, treat that as a signal to bring in a real
library rather than extend this file by hand -- hand-rolled crypto is fine for one
well-scoped algorithm, not for a growing feature set.
"""
import base64
import hashlib
import hmac
import json
import os
import time


class TokenError(Exception):
    """Raised for any invalid/expired/malformed token. Deliberately one exception
    type: the caller (server.py) always wants to do the same thing -- return 401 --
    regardless of which specific check failed. Distinguishing reasons is useful in
    logs, not in control flow, so the message carries the detail instead."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def _secret():
    """Read fresh on every call rather than caching at import time, so a secret
    rotated in the deploy environment takes effect on next request, not next restart."""
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise TokenError("JWT_SECRET not set in environment")
    return secret.encode()


def create_token(claims: dict, expires_in: int = 3600) -> str:
    """claims: whatever you want in the payload (e.g. {"sub": "jash"}).
    expires_in: seconds from now until the token is rejected as expired.

    This is a standalone minting function, not exposed as a server endpoint --
    deliberately. An endpoint that issues tokens is itself an attack surface (whoever
    can call it can mint valid credentials); this project has no user database or
    password check to gate that endpoint with, so minting stays an offline, operator-run
    step (see mint_token.py) until real user accounts exist.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = dict(claims)
    payload.setdefault("iat", now)
    payload["exp"] = now + expires_in

    segments = [
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode()
    sig = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
    segments.append(_b64url_encode(sig))
    return ".".join(segments)


def verify_token(token: str) -> dict:
    """Returns the decoded payload on success. Raises TokenError on any failure --
    bad signature, malformed structure, or expiry. Always checked in that order:
    signature first, so an attacker can't use the error message ("expired" vs
    "malformed") to probe token structure without already holding a validly-signed one."""
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise TokenError("malformed token (expected 3 dot-separated segments)")

    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception:
        raise TokenError("malformed signature encoding")

    # constant-time compare -- a naive == here would leak timing information an
    # attacker could use to forge a valid signature byte-by-byte.
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise TokenError("invalid signature")

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        raise TokenError("malformed payload encoding")

    exp = payload.get("exp")
    if exp is not None and time.time() > exp:
        raise TokenError("token expired")

    return payload


def bearer_token_from_header(auth_header: str) -> str:
    """Pulls the token out of an 'Authorization: Bearer <token>' header value.
    Raises TokenError if the header is missing or malformed, so callers can treat
    'no header' and 'bad token' identically (both -> 401)."""
    if not auth_header or not auth_header.startswith("Bearer "):
        raise TokenError("missing or malformed Authorization header")
    return auth_header[len("Bearer "):].strip()