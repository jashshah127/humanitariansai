"""
PROBLEM LOG -- writes every solved problem to Supabase's problems_log, then tags it.

Flow for one /solve (classification plan, doc 09 section 2):
  1. clean the text (redact.py) -- only the stored copy; the solver had the original
  2. insert the row UNTAGGED, so the problem is counted even if tagging fails later
  3. classify the cleaned text (card-first, see classifier.py)
  4. update the row with the tags
If the model is down, the row simply stays untagged; a later run can tag it.

WHY A BACKGROUND WORKER: tagging is a model call (seconds, sometimes a timeout), and the
student must never wait for it. ProblemLogger hands each solve to ONE worker thread
through a BOUNDED queue:
  - one worker  -> model calls go one at a time, which also spares the shared quota
  - bounded     -> under a burst the queue cannot grow without limit; when it is full,
                   new entries are dropped and counted (`dropped`), never blocking /solve
  - one shared GeminiClassifierLLM -> its circuit breaker remembers a failing model
                   across requests (a fresh client per call would forget every time)

WHY THE SECRET KEY: problems_log has no insert or update policy, so browsers (publishable
key) cannot write to it at all. Only the server, holding SUPABASE_SECRET_KEY, can. That
key bypasses RLS, so it must live only in server environment variables -- never in the
browser, never in the repo. Without it, logging is simply off.
"""
import json
import os
import queue
import sys
import threading
import traceback
import urllib.error
import urllib.request

from classifier import ClassifyError, GeminiClassifierLLM, classify
from redact import redact


class LogError(Exception):
    """Supabase refused or could not be reached."""


def configured():
    """Logging is on only when the server has both the project URL and the secret key."""
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SECRET_KEY"))


def _urllib_fetch(method, url, headers, body, timeout):
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class SupabaseLogStore:
    """insert/update rows in problems_log through the REST API. `fetch` is injectable so
    tests run with no network; defaults to urllib."""

    def __init__(self, url=None, key=None, fetch=None, timeout=10):
        self.url = (url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.key = key or os.environ.get("SUPABASE_SECRET_KEY", "")
        self._fetch, self.timeout = fetch or _urllib_fetch, timeout

    def _call(self, method, path, row, prefer):
        headers = {"apikey": self.key, "Content-Type": "application/json", "Prefer": prefer}
        try:
            status, raw = self._fetch(method, f"{self.url}/rest/v1/{path}", headers,
                                      json.dumps(row).encode(), self.timeout)
        except (TimeoutError, urllib.error.URLError, ConnectionError, OSError) as e:
            raise LogError(f"{method} problems_log: {type(e).__name__}")
        if not 200 <= status < 300:
            # Keep only the error code and short message. The body's "details" can quote
            # the whole failing row -- problem text included -- and this ends up in logs.
            try:
                err = json.loads(raw)
                why = f"{err.get('code')} {err.get('message', '')}"[:200]
            except (ValueError, AttributeError):
                why = "unreadable error body"
            raise LogError(f"{method} problems_log: HTTP {status} {why}")
        return raw

    def insert(self, row):
        """Insert one row; returns its id."""
        raw = self._call("POST", "problems_log?select=id", row, "return=representation")
        return json.loads(raw)[0]["id"]

    def update(self, row_id, fields):
        self._call("PATCH", f"problems_log?id=eq.{row_id}", fields, "return=minimal")


def build_row(query, result):
    """The untagged row for one solve, and the cleaned text the tagger will see."""
    clean, count = redact(query)
    row = {"problem_text": clean, "redactions": count, "verification": result["verification"]}
    solution = result.get("trace") or {}
    if solution.get("route") == "deterministic_script":
        row["matched_card"] = (solution.get("retrieve") or {}).get("matched")
    return row, clean


def tag_fields(c):
    """Classification -> the columns the tagger fills in."""
    return {"topic": c.topic, "subtopic": c.subtopic, "grade_level": c.grade_level,
            "difficulty": c.difficulty, "tag_model": c.model, "tag_source": c.source,
            "needs_review": c.needs_review, "review_reason": c.review_reason}


def log_and_tag(query, result, store, llm=None):
    """Steps 1-4 for one solve. Returns "skipped", "untagged" or "tagged".
    A store failure raises LogError (the worker reports it and carries on)."""
    if not (query or "").strip():
        return "skipped"
    row, clean = build_row(query, result)
    row_id = store.insert(row)
    try:
        c = classify(clean, solution=result.get("trace"), llm=llm)
    except ClassifyError as e:   # counted, just not tagged; a later run can fill it in
        print(f"[problem_log] row {row_id} left untagged: {e}", file=sys.stderr)  # no text
        return "untagged"
    store.update(row_id, tag_fields(c))
    return "tagged"


class ProblemLogger:
    """One background worker behind a bounded queue. submit() never blocks or raises."""

    def __init__(self, store, llm=None, maxsize=100):
        self.store, self.llm = store, llm or GeminiClassifierLLM()
        self._q = queue.Queue(maxsize=maxsize)
        self.dropped = 0
        self.outcomes = {}       # "tagged"/"untagged"/"skipped"/"failed" -> count
        threading.Thread(target=self._run, name="problem-log", daemon=True).start()

    def submit(self, query, result):
        try:
            self._q.put_nowait((query, result))
        except queue.Full:
            self.dropped += 1

    def _run(self):
        while True:
            query, result = self._q.get()
            try:
                outcome = log_and_tag(query, result, self.store, self.llm)
            except Exception:    # one bad entry must never stop the worker
                traceback.print_exc()
                outcome = "failed"
            self.outcomes[outcome] = self.outcomes.get(outcome, 0) + 1
            self._q.task_done()  # last, so wait() returns only after the count is in

    def wait(self):
        """Block until every submitted entry is processed (tests and shutdown only)."""
        self._q.join()

    def pending(self):
        """Entries queued or in progress -- lets an operator see the worker has caught up."""
        return self._q.unfinished_tasks
