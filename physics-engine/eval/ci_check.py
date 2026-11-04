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


def me_reports_role():
    """GET /me must report who called and their role: a Supabase user's role comes from
    their own profile; a minted (operator) token has no role; a failed lookup is not a 'user'."""
    sys.path.insert(0, os.path.join(HERE, ".."))
    import server
    import supabase_auth
    from jwt_auth import create_token

    class FakeHandler:
        def __init__(self, auth):
            self.headers = {"Authorization": auth}
            self.status = None

        def _send(self, code, payload):
            self.status = code

    profile_reply = {"value": (200, b'[{"role": "admin"}]')}

    def fake_fetch(url, headers, timeout):
        if url.endswith("/auth/v1/user"):
            return 200, b'{"id": "u1", "email": "admin@test.dev"}'
        if "/rest/v1/profiles" in url:
            r = profile_reply["value"]
            if isinstance(r, Exception):
                raise r
            return r
        return 404, b"{}"

    def me(auth):
        h = FakeHandler(auth)
        if not server._authenticate(h):
            return ("status", h.status)
        return server.api_me(h.caller)

    real_fetch, supabase_auth._urllib_fetch = supabase_auth._urllib_fetch, fake_fetch
    try:
        with _EnvPatch(JWT_SECRET="ci-secret", SUPABASE_URL="http://supabase.test",
                       SUPABASE_PUBLISHABLE_KEY="pk"):
            got_admin = me("Bearer supabase-token")
            profile_reply["value"] = (200, b'[{"role": "user"}]')
            got_user = me("Bearer supabase-token")
            profile_reply["value"] = (200, b"[]")
            got_none = me("Bearer supabase-token")
            got_minted = me("Bearer " + create_token({"sub": "ci"}, expires_in=60))
            profile_reply["value"] = TimeoutError()
            try:
                me("Bearer supabase-token")
                got_down = "no error"
            except supabase_auth.AuthUnavailable:
                got_down = "unavailable"
    finally:
        supabase_auth._urllib_fetch = real_fetch

    checks = {
        "admin": (got_admin, {"kind": "supabase", "id": "u1", "email": "admin@test.dev", "role": "admin"}),
        "user": (got_user.get("role") if isinstance(got_user, dict) else got_user, "user"),
        "no profile": (got_none.get("role") if isinstance(got_none, dict) else got_none, None),
        "minted": (got_minted, {"kind": "minted", "sub": "ci", "role": None}),
        "lookup down": (got_down, "unavailable"),
    }
    wrong = {k: got for k, (got, want) in checks.items() if got != want}
    if wrong:
        return False, f"wrong /me result for: {wrong}"
    return True, "admin/user role from own profile; minted -> no role; lookup failure -> unavailable"


def classifier_labels_match_db():
    """The classifier's allowed (topic, subtopic) pairs must be exactly the rows the
    problems_log migration seeds into public.topics -- otherwise tags fail the foreign key."""
    import re
    from classifier import TOPIC_PAIRS
    path = os.path.join(HERE, "..", "supabase", "migrations", "20261022164924_problems_log.sql")
    seeded = set(re.findall(r"\('([^']+)', '([^']+)'\)", open(path).read()))
    ours = set(TOPIC_PAIRS)
    if ours != seeded:
        return False, f"only in classifier: {sorted(ours - seeded)}; only in db: {sorted(seeded - ours)}"
    return True, f"{len(ours)} pairs, identical to the topics table seed"


def classifier_rules():
    """Card label wins; disagreement, Other and invalid pairs are flagged; a failed model
    still yields the card's topic; no card + failed model -> ClassifyError."""
    import json
    from classifier import classify, ClassifyError
    from pipeline import solve_physics_problem
    atwood = solve_physics_problem("c", "atwood", {"m1": 4, "m2": 6, "g": 9.8}, ["a", "T"],
                                   topic_hint="Mechanics")

    def model(**tags):
        reply = {"grade_level": "intro_undergrad", "difficulty": "easy", "confidence": 0.9, **tags}
        return lambda prompt, schema: (json.dumps(reply), "fake-model")

    def failing(prompt, schema):
        raise ClassifyError("down")

    cases = {}
    r = classify("pulley", atwood, model(topic="Mechanics", subtopic="Dynamics"))
    cases["card, model agrees"] = ((r.topic, r.subtopic, r.source, r.needs_review, r.grade_level),
                                   ("Mechanics", "Dynamics", "engine_card", False, "intro_undergrad"))
    r = classify("pulley", atwood, model(topic="E&M", subtopic="Circuits"))
    cases["card, model disagrees"] = ((r.topic, r.subtopic, r.needs_review), ("Mechanics", "Dynamics", True))
    r = classify("pulley", atwood, failing)
    cases["card, model down"] = ((r.topic, r.grade_level, r.source), ("Mechanics", None, "engine_card"))
    r = classify("charged ball", None, model(topic="E&M", subtopic="Electrostatics"))
    cases["no card, valid pair"] = ((r.topic, r.subtopic, r.source, r.needs_review),
                                    ("E&M", "Electrostatics", "llm", False))
    r = classify("hydrogen", None, model(topic="Other", subtopic="Other"))
    cases["no card, Other"] = ((r.topic, r.needs_review), ("Other", True))
    r = classify("x", None, model(topic="Mechanics", subtopic="Circuits"))
    cases["no card, invalid pair"] = ((r.topic, r.subtopic, r.needs_review), ("Other", "Other", True))
    r = classify("x", None, model(topic="Mechanics", subtopic="Kinematics", grade_level="phd"))
    cases["unknown grade dropped"] = (r.grade_level, None)
    try:
        classify("x", None, failing)
        cases["no card, model down"] = ("no error", "ClassifyError")
    except ClassifyError:
        cases["no card, model down"] = ("ClassifyError", "ClassifyError")

    wrong = {k: got for k, (got, want) in cases.items() if got != want}
    if wrong:
        return False, f"wrong for: {wrong}"
    return True, "card label wins; disagreement/Other/invalid pair flagged; failures handled"


def classifier_model_failures():
    """Retry 503 and timeouts, skip a model on 429/404, stop on other errors -- offline."""
    import json
    from classifier import GeminiClassifierLLM, ClassifyError
    ok = (200, json.dumps({"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}).encode())

    def run(script):
        """script: {model: [reply, reply, ...]}; returns (result, calls in order)."""
        calls = []

        def post(url, body, headers, timeout):
            model = url.split("/models/")[1].split(":")[0]
            calls.append(model)
            r = script[model].pop(0)
            if isinstance(r, Exception):
                raise r
            return r

        llm = GeminiClassifierLLM(models=list(script), waits=(0, 0), post=post, sleep=lambda s: None)
        try:
            return llm("p", {})[1], calls
        except ClassifyError as e:
            return f"error: {str(e)[:40]}", calls

    with _EnvPatch(GEMINI_API_KEY="test-key"):
        cases = {
            "503 then ok": (run({"m1": [(503, b""), ok]}), ("m1", ["m1", "m1"])),
            "timeout then ok": (run({"m1": [TimeoutError(), ok]}), ("m1", ["m1", "m1"])),
            "429 skips model": (run({"m1": [(429, b"")], "m2": [ok]}), ("m2", ["m1", "m2"])),
            "404 skips model": (run({"m1": [(404, b"")], "m2": [ok]}), ("m2", ["m1", "m2"])),
            "503 x3 then next": (run({"m1": [(503, b"")] * 3, "m2": [ok]}), ("m2", ["m1", "m1", "m1", "m2"])),
        }
        res, calls = run({"m1": [(400, b"")], "m2": [ok]})
        cases["400 stops at once"] = ((res.startswith("error"), calls), (True, ["m1"]))

        # Circuit breaker: one llm, several calls, a fake clock.
        now = {"t": 0.0}
        calls = []

        def post(url, body, headers, timeout):
            model = url.split("/models/")[1].split(":")[0]
            calls.append(model)
            if model == "m1":
                raise TimeoutError()          # m1 never answers
            return ok

        llm = GeminiClassifierLLM(models=["m1", "m2"], waits=(0, 0), post=post, sleep=lambda s: None,
                                  cooldown=300, clock=lambda: now["t"])
        llm("p", {})
        first = list(calls); calls.clear()
        llm("p", {})                           # m1 failed recently -> straight to m2
        second = list(calls); calls.clear()
        now["t"] = 301                         # cooldown over -> m1 gets another chance
        llm("p", {})
        third = list(calls)
        cases["circuit: 1st call retries m1 then m2"] = (first, ["m1", "m1", "m1", "m2"])
        cases["circuit: 2nd call skips m1"] = (second, ["m2"])
        cases["circuit: after cooldown, m1 retried"] = (third[0], "m1")
    wrong = {k: got for k, (got, want) in cases.items() if got != want}
    if wrong:
        return False, f"wrong for: {wrong}"
    return True, "503/timeout retried; 429/404 skip model; other errors stop; failed model skipped during cooldown"


def redaction_rules():
    """Personal details are replaced and counted; physics numbers are never touched;
    a second pass changes nothing."""
    from redact import redact
    pii = {
        "Email jane.doe+hw@husky.neu.edu now": ("Email [EMAIL] now", 1),
        "See https://drive.google.com/d/abc?x=1, then": ("See [LINK], then", 1),
        "Call 617-555-1234.": ("Call [PHONE].", 1),
        "Call (617) 555-1234": ("Call [PHONE]", 1),
        "Call +1 617 555 1234": ("Call [PHONE]", 1),
        "My NUID is 002123456.": ("My NUID is [ID].", 1),
        "SSN 123-45-6789": ("SSN [ID]", 1),
        "I'm jane@uni.edu, NUID 002123456, cell 617.555.1234: a 2 kg block":
            ("I'm [EMAIL], NUID [ID], cell [PHONE]: a 2 kg block", 3),
    }
    physics = [
        "A 1500-kg car accelerates at 9.8 m/s^2 for 12.5 s.",
        "c = 300000000 m/s and G = 6.67e-11 N m^2/kg^2",
        "Charges q1 = +3.0e-6 C and q2 = -2.0e-6 C, 0.050 m apart; range 1.2-3.4 m.",
        "Voltage 120 V, 60 Hz, 2023-11-03 lab, resistors 100 200 3000 ohm",
    ]
    wrong = {s: redact(s) for s, want in pii.items() if redact(s) != want}
    wrong.update({s: redact(s) for s in physics if redact(s) != (s, 0)})
    wrong.update({s: "second pass changed it" for s, (out, _) in pii.items() if redact(out) != (out, 0)})
    if wrong:
        return False, f"wrong for: {wrong}"
    return True, "emails/links/phones/IDs replaced and counted; physics numbers untouched; second pass is a no-op"


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
    check("GET /me reports role", me_reports_role)
    print("\nClassifier invariants")
    check("classifier labels match the topics table", classifier_labels_match_db)
    check("classifier rules", classifier_rules)
    check("classifier model failures", classifier_model_failures)
    print("\nLogging invariants")
    check("redaction rules", redaction_rules)

    print()
    if failures:
        print(f"FAILED: {len(failures)} -> {failures}")
        sys.exit(1)
    print("All checks passed.")
