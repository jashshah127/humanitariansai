"""
EVENT LOG -- the Phase 1 addition the brief singles out: "Adding one thing to Phase 1
-- the event log -- turns the pipeline's own output into the data source for four loops
later." Built now, while it is cheap, so the loops have history to run against when they
arrive instead of starting from an empty table.

THE DESIGN DECISION WORTH DEFENDING: identity scope is enforced by the code, not
described in a document. The brief's telemetry table assigns every metric an identity
column (None / Aggregate / Persistent) and says "a metric earns a row in this table
before it earns a line of logging code." A table in a document cannot stop a future
contributor from attaching student_id to a card-usage event during a late-night debug
session. This module can, and does -- emitting a NONE-scope event with a student_id
raises rather than quietly widening the FERPA surface the brief committed to keeping
narrow.

Storage is deliberately pluggable and defaults to in-memory. Where these events
ultimately land is a real decision with retention and data-processing-agreement
implications (Q6, still open with Prof. Sri/Nik) -- so this module makes the events,
and declines to pick their destination.
"""
import json
import time
import uuid
from enum import Enum


class IdentityScope(str, Enum):
    """Mirrors the Identity column of the brief's telemetry table."""
    NONE = "none"              # no identity at all -- curate-loop and system telemetry
    AGGREGATE = "aggregate"    # session-level; analytical view never exposes a person
    PERSISTENT = "persistent"  # tied to a student across sessions -- learn loop, grade mode


# event name -> (identity scope, which brief-table metric it powers, phase it starts)
EVENT_REGISTRY = {
    # ---- Phase 1
    "query.received":     (IdentityScope.AGGREGATE, "session length, questions per session", 1),
    "parse.completed":    (IdentityScope.NONE,      "parse health", 1),
    "parse.failed":       (IdentityScope.NONE,      "parse health", 1),
    "route.decided":      (IdentityScope.NONE,      "mode/route split", 1),
    "query.completed":    (IdentityScope.NONE,      "query latency (time to solve)", 1),

    # ---- Phase 2 (emitted now; the dashboards that read them come later)
    "retrieve.candidates":  (IdentityScope.NONE, "card usage rate", 2),
    "plan.closure_gap":     (IdentityScope.NONE, "re-plan rate", 2),
    "verify.failed_check":  (IdentityScope.NONE, "verify-failure breakdown by check type", 2),
    "curate.no_card_match": (IdentityScope.NONE, "fallback rate; syllabus coverage denominator", 2),
    "solution.verified_pair": (IdentityScope.NONE, "verified (problem, solution) accumulation", 2),
}


class ScopeViolation(Exception):
    """Raised when an event is given identity it is not permitted to carry."""


class EventLog:
    def __init__(self, sink=None):
        """sink: callable(event_dict) -> None. Defaults to in-memory collection.
        Where events actually persist is deliberately not decided here -- see Q6."""
        self.events = []
        self.sink = sink

    def emit(self, name, session_id=None, student_id=None, **fields):
        if name not in EVENT_REGISTRY:
            raise ValueError(
                f"unregistered event '{name}'. Add it to EVENT_REGISTRY with an identity "
                f"scope and the metric it powers -- per the brief, a metric earns a row in "
                f"the telemetry table before it earns a line of logging code."
            )
        scope, powers, phase = EVENT_REGISTRY[name]

        if student_id is not None and scope is not IdentityScope.PERSISTENT:
            raise ScopeViolation(
                f"event '{name}' is scope={scope.value} and must not carry student_id. "
                f"If this event genuinely needs to be student-linked, that is a change to "
                f"the brief's telemetry table and its FERPA footprint -- make it there first."
            )
        if session_id is not None and scope is IdentityScope.NONE:
            raise ScopeViolation(
                f"event '{name}' is scope=none and must not carry session_id."
            )

        event = {
            "event_id": str(uuid.uuid4()),
            "name": name,
            "ts": time.time(),
            "scope": scope.value,
            "powers": powers,
            "phase": phase,
            **fields,
        }
        if session_id is not None:
            event["session_id"] = session_id
        if student_id is not None:
            event["student_id"] = student_id

        self.events.append(event)
        if self.sink:
            self.sink(event)
        return event

    # -- convenience readers ------------------------------------------------
    def by_name(self, name):
        return [e for e in self.events if e["name"] == name]

    def coverage_gaps(self):
        """Everything the curate loop would pick up: problems no card matched."""
        return self.by_name("curate.no_card_match")

    def latency_summary(self):
        done = self.by_name("query.completed")
        if not done:
            return None
        times = [e["duration_ms"] for e in done if "duration_ms" in e]
        if not times:
            return None
        times.sort()
        return {
            "n": len(times),
            "median_ms": times[len(times) // 2],
            "max_ms": times[-1],
            "mean_ms": sum(times) / len(times),
        }

    def route_split(self):
        counts = {}
        for e in self.by_name("route.decided"):
            counts[e["route"]] = counts.get(e["route"], 0) + 1
        return counts

    def to_jsonl(self):
        return "\n".join(json.dumps(e) for e in self.events)
