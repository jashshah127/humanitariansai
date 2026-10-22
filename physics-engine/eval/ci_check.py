"""
One command, every invariant. Run before any push.

    python3 eval/ci_check.py

Exits non-zero on any failure, so it can gate a commit hook or an Action.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))

failures = []


def check(label, fn):
    try:
        ok, detail = fn()
    except Exception as e:  # noqa: BLE001 - a crashing check is a failing check
        ok, detail = False, f"{type(e).__name__}: {e}"
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {detail}")
    if not ok:
        failures.append(label)


def golden_set_16():
    out = subprocess.run([sys.executable, os.path.join(HERE, "demo.py")],
                         capture_output=True, text=True)
    hit = "16/16 problems solved" in out.stdout
    return hit, "16/16 golden-set problems" if hit else "golden set regressed"


def determinism():
    from pipeline import solve_physics_problem
    import json
    runs = {json.dumps(solve_physics_problem("d", "d", dict(m1=4, m2=6, g=9.8),
                                             ["a", "T"], topic_hint="Mechanics"),
                       sort_keys=True) for _ in range(10)}
    return len(runs) == 1, f"10 identical runs" if len(runs) == 1 else "NON-DETERMINISTIC"


def ambiguity_caught():
    from pipeline import solve_physics_problem
    r = solve_physics_problem("amb", "amb",
                              dict(v0=0, a=2.5, t=12, m=2, k=500, x=0.15), ["v"],
                              topic_hint="Mechanics")
    ok = r["route"] == "ambiguous_multiple_deterministic_paths"
    return ok, "conflicting formulas flagged, not silently resolved" if ok else r["route"]


def units_consistent():
    from units import audit_units
    from formula_kb import ALL_CARDS
    from variable_glossary import GLOSSARY
    f = audit_units(ALL_CARDS, GLOSSARY)
    n = len(f["unparseable"]) + len(f["card_vs_glossary"])
    return n == 0, "no unit/dimension contradictions" if n == 0 else f"{n} findings: {f}"


def glossary_covers_cards():
    from variable_glossary import audit_symbol_collisions
    from formula_kb import ALL_CARDS
    a = audit_symbol_collisions(ALL_CARDS)
    ok = not a["undocumented"]
    return ok, ("every card variable is documented; "
                f"{len(a['output_collisions'])} known output collisions under arbitration") \
        if ok else f"parser can't be told to emit: {a['undocumented']}"


def symbolic_coverage():
    from pipeline import symbolic_solution
    from formula_kb import ALL_CARDS
    missing = [c.id for c in ALL_CARDS if symbolic_solution(c)[0] is None]
    ok = not missing
    return ok, (f"all {len(ALL_CARDS)} cards solve symbolically (general formula, not just "
                f"a number)") if ok else f"no symbolic solution for: {missing}"


def symbolic_input_mode():
    """Problems stated in symbols rather than numbers must solve, not decline."""
    import sympy as sp
    from pipeline import solve_physics_problem
    kn = dict(m1=sp.Symbol("m1"), m2=sp.Symbol("m2"), g=sp.Symbol("g"))
    r = solve_physics_problem("s", "symbolic atwood", kn, ["a", "T"], topic_hint="Mechanics")
    if r["route"] != "deterministic_script":
        return False, f"symbolic problem declined (route={r['route']})"
    if not r["solve"]["symbolic_mode"]:
        return False, "symbolic_mode flag not set"
    if not r["verify"]["residual_check"]["ok"]:
        return False, "symbolic residual identity did not simplify to zero"
    ans = r["final_answer"].get("T", "")
    if "m1" not in str(ans) or "m2" not in str(ans):
        return False, f"symbolic answer looks wrong: T = {ans}"
    return True, f"solves symbolically; T = {ans}, verified as an identity"


def grade_mode_works():
    from grade_mode import grade, Assessment
    kn = dict(m1=4, m2=6, g=9.8)
    ok_case = grade("g", "atwood", kn, ["a", "T"], {"a": 1.96, "T": 47.04},
                    topic_hint="Mechanics")
    if ok_case.assessment != Assessment.CORRECT:
        return False, f"correct submission graded as {ok_case.assessment}"

    flip = grade("g", "atwood", kn, ["a", "T"], {"a": -1.96, "T": 47.04},
                 topic_hint="Mechanics")
    if flip.misconception != "sign_flip":
        return False, f"sign-flip misconception not detected (got {flip.misconception})"

    # The one that matters most: it must REFUSE to grade when it has no verified
    # reference. Marking a student wrong against an unverified answer is the project's
    # own failure mode pointed at someone's transcript.
    refuse = grade("g", "damped", dict(m=0.5, k=200, c_damp=1.2),
                   ["damped_frequency"], {"damped_frequency": 19.9})
    if refuse.assessment != Assessment.NOT_ASSESSABLE:
        return False, "graded a problem with no verified reference -- must refuse"
    return True, "correct/misconception/refuse-to-grade all behave"


def grade_feedback_safe():
    """Grade feedback must never contain the correct value (the UI decides when the
    student sees it), a partial answer must not be graded "correct", and only the
    asked-for quantities count."""
    from grade_mode import grade, Assessment
    kn = dict(m1=4, m2=6, g=9.8)
    wrong = grade("g", "atwood", kn, ["a", "T"], {"a": 3.0, "T": 47.04},
                  topic_hint="Mechanics")
    if wrong.assessment != Assessment.WRONG_VALUE:
        return False, f"wrong value graded as {wrong.assessment}"
    if "1.96" in wrong.feedback or "47.0" in wrong.feedback:
        return False, f"feedback reveals the answer: {wrong.feedback!r}"
    partial = grade("g", "atwood", kn, ["a", "T"], {"a": 1.96}, topic_hint="Mechanics")
    if partial.assessment != Assessment.INCOMPLETE or partial.missing != ["T"]:
        return False, f"partial answer graded as {partial.assessment}, missing={partial.missing}"
    only_a = grade("g", "atwood", kn, ["a"], {"a": 1.96}, topic_hint="Mechanics")
    if only_a.assessment != Assessment.CORRECT or set(only_a.reference_answer) != {"a"}:
        return False, "a quantity that wasn't asked for was required or revealed"
    if only_a.verification != "verified" or wrong.verification != "verified":
        return False, "a graded result is missing its verified badge"
    return True, "no answer in feedback; partial = incomplete; only asked quantities graded"


def grade_api_parses_once():
    """/parse then /grade must cost ONE model call and /parse must not leak the answer."""
    import json
    sys.path.insert(0, os.path.join(HERE, ".."))
    import server
    from parse import StubLLM
    stub = StubLLM({"pulley": {"knowns": {"m1": 4, "m2": 6}, "unknowns": ["a", "T"],
                               "topic_hint": "Mechanics", "sources": {}}})
    real_llm, server._llm = server._llm, (lambda: stub)
    try:
        q = "Two blocks of 4 kg and 6 kg hang from a frictionless pulley."
        setup = server.api_parse({"query": q})
        if not setup["gradable"]:
            return False, f"Atwood problem reported as not gradable: {setup['reason']}"
        if "1.96" in json.dumps(setup) or "47.0" in json.dumps(setup):
            return False, "/parse response contains the answer"
        result = server.api_grade({"query": q, "parsed": setup["parsed"],
                                   "student_answer": {"a": 1.96, "T": 47.04}})
    finally:
        server._llm = real_llm
    if result["assessment"] != "correct":
        return False, f"round trip graded as {result['assessment']}"
    if len(stub.calls) != 1:
        return False, f"{len(stub.calls)} model calls for one parse + grade (want 1)"
    return True, "/parse -> /grade uses one model call and never sends the answer early"


class _EnvPatch:
    """Set / unset environment variables for one check, then put them back."""

    def __init__(self, **values):
        self.values, self.saved = values, {}

    def __enter__(self):
        for k, v in self.values.items():
            self.saved[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def __exit__(self, *exc):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def supabase_token_rules():
    """Each Supabase Auth reply must map to the right outcome -- offline, via a fake fetch.
    401/403 is the caller's fault (TokenError -> 401); anything else is ours (-> 503)."""
    from supabase_auth import verify_supabase_token, AuthUnavailable
    from jwt_auth import TokenError

    def reply(status, body=b"{}"):
        return lambda url, headers, timeout: (status, body)

    def no_answer(url, headers, timeout):
        raise TimeoutError()

    cases = [("signed-in user", reply(200, b'{"id": "u1", "email": "a@test.dev"}'), "ok"),
             ("signed out (403)", reply(403), TokenError),
             ("expired/forged (401)", reply(401), TokenError),
             ("Supabase error (500)", reply(500), AuthUnavailable),
             ("timeout", no_answer, AuthUnavailable)]
    with _EnvPatch(SUPABASE_URL="http://supabase.test", SUPABASE_PUBLISHABLE_KEY="pk"):
        for label, fetch, want in cases:
            try:
                got = "ok" if verify_supabase_token("t", fetch=fetch)["id"] == "u1" else "bad user"
            except (TokenError, AuthUnavailable) as e:
                got = type(e)
            if got != want:
                return False, f"{label}: got {getattr(got, '__name__', got)}"
    with _EnvPatch(SUPABASE_URL=None, SUPABASE_PUBLISHABLE_KEY=None):
        try:
            verify_supabase_token("t", fetch=reply(200))
            return False, "accepted a token with Supabase not configured"
        except AuthUnavailable:
            pass
    return True, "200 -> user; 401/403 -> rejected; 500/timeout/unconfigured -> unavailable"


def server_auth_paths():
    """server.py must accept minted AND Supabase tokens, answer 401 for a bad token and
    503 when Supabase can't be asked -- and never call Supabase for a minted token."""
    sys.path.insert(0, os.path.join(HERE, ".."))
    import server
    import supabase_auth
    from jwt_auth import create_token

    class FakeHandler:
        def __init__(self, auth):
            self.headers = {"Authorization": auth} if auth else {}
            self.status = None

        def _send(self, code, payload):
            self.status = code

    calls = []
    supabase_reply = {"value": (200, b'{"id": "u1"}')}

    def fake_fetch(url, headers, timeout):
        calls.append(url)
        r = supabase_reply["value"]
        if isinstance(r, Exception):
            raise r
        return r

    def run(auth):
        h = FakeHandler(auth)
        return ("allowed" if server._authenticate(h) else h.status)

    real_fetch, supabase_auth._urllib_fetch = supabase_auth._urllib_fetch, fake_fetch
    try:
        with _EnvPatch(JWT_SECRET="ci-secret", SUPABASE_URL="http://supabase.test",
                       SUPABASE_PUBLISHABLE_KEY="pk"):
            minted = create_token({"sub": "ci"}, expires_in=60)
            results = {"no header": (run(None), 401),
                       "minted token": (run(f"Bearer {minted}"), "allowed")}
            if calls:
                return False, "a minted token triggered a Supabase call"
            results["Supabase session"] = (run("Bearer supabase-token"), "allowed")
            supabase_reply["value"] = (403, b'{"error_code": "session_not_found"}')
            results["signed-out session"] = (run("Bearer supabase-token"), 401)
            supabase_reply["value"] = TimeoutError()
            results["Supabase unreachable"] = (run("Bearer supabase-token"), 503)
        with _EnvPatch(JWT_SECRET="ci-secret", SUPABASE_URL=None, SUPABASE_PUBLISHABLE_KEY=None):
            results["Supabase not configured"] = (run("Bearer supabase-token"), 401)
    finally:
        supabase_auth._urllib_fetch = real_fetch

    wrong = {k: got for k, (got, want) in results.items() if got != want}
    if wrong:
        return False, f"wrong outcome for: {wrong}"
    return True, "minted + Supabase tokens accepted; bad -> 401; Supabase down -> 503; minted never calls Supabase"


def identity_scoping_enforced():
    from event_log import EventLog, ScopeViolation
    log = EventLog()
    try:
        log.emit("curate.no_card_match", student_id="s1", unknowns=["v"])
        return False, "SCOPE VIOLATION ALLOWED -- student_id accepted on a none-scope event"
    except ScopeViolation:
        pass
    try:
        log.emit("not.a.registered.event", foo=1)
        return False, "unregistered event accepted"
    except ValueError:
        return True, "student_id rejected on none-scope events; unregistered events rejected"


def phase1_end_to_end():
    out = subprocess.run([sys.executable, os.path.join(HERE, "demo_phase1.py")],
                         capture_output=True, text=True)
    hit = "5/5 problems parsed from raw text AND solved correctly" in out.stdout
    gap = "coverage gaps  : 1" in out.stdout
    if hit and gap:
        return True, "raw text -> answer for all 5 in-scope; out-of-scope one logged as a gap"
    return False, "phase 1 end-to-end regressed"


if __name__ == "__main__":
    print("Phase 0 invariants")
    check("golden set", golden_set_16)
    check("determinism", determinism)
    check("ambiguity routing", ambiguity_caught)
    print("\nPhase 1 invariants")
    check("end-to-end from raw text", phase1_end_to_end)
    check("unit/dimension consistency", units_consistent)
    check("symbolic coverage", symbolic_coverage)
    check("symbolic input mode", symbolic_input_mode)
    check("glossary covers every card variable", glossary_covers_cards)
    check("identity scoping enforced", identity_scoping_enforced)
    print("\nPhase 2 invariants")
    check("grade mode", grade_mode_works)
    check("grade feedback hides the answer", grade_feedback_safe)
    check("grade API parses once", grade_api_parses_once)
    print("\nAuth invariants")
    check("Supabase token rules", supabase_token_rules)
    check("server auth paths", server_auth_paths)

    print()
    if failures:
        print(f"FAILED: {len(failures)} -> {failures}")
        sys.exit(1)
    print("All checks passed.")
