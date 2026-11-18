"""
GUEST LIMITS -- how many problems a guest (anonymous Supabase user) may still solve.

The count lives in Supabase (migration 20261118120000_guest_access): one database
function, use_guest_problem(), checks AND counts in a single locked step, per guest and
for all guests per day. Browsers can't run it; only the server can, with the secret key.

With no CAPTCHA, the daily total is the real protection: new guests are free to create,
so a per-guest limit alone never caps the total.

Standard library only, like supabase_auth.py and problem_log.py.
"""
import json
import os
import urllib.error
import urllib.request

TIMEOUT_S = 5


class GuestCheckUnavailable(Exception):
    """The count couldn't be checked: not configured, timeout, outage, or an odd reply."""


def configured():
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SECRET_KEY"))


def _urllib_post(url, headers, body, timeout):
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def use_guest_problem(user_id, per_guest, daily, post=None):
    """Count one problem for this guest. Returns {"status": ..., "remaining": ...}, where
    status is "ok", "guest_limit", "daily_limit" or "not_guest".
    Raises GuestCheckUnavailable if Supabase can't be asked."""
    if not configured():
        raise GuestCheckUnavailable("SUPABASE_URL / SUPABASE_SECRET_KEY not set")
    url = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/rpc/use_guest_problem"
    headers = {"apikey": os.environ["SUPABASE_SECRET_KEY"], "Content-Type": "application/json"}
    body = json.dumps({"p_user": user_id, "p_per_guest": per_guest, "p_daily": daily}).encode()
    try:
        status, raw = (post or _urllib_post)(url, headers, body, TIMEOUT_S)
    except (TimeoutError, urllib.error.URLError, ConnectionError, OSError) as e:
        raise GuestCheckUnavailable(f"could not reach Supabase: {type(e).__name__}")
    if status != 200:
        raise GuestCheckUnavailable(f"use_guest_problem answered {status}")
    try:
        reply = json.loads(raw)
    except ValueError:
        raise GuestCheckUnavailable("unreadable reply from use_guest_problem")
    if not isinstance(reply, dict) or "status" not in reply:
        raise GuestCheckUnavailable("unexpected reply from use_guest_problem")
    return reply