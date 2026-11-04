"""
Row-level security tests -- run against the LOCAL Supabase stack.

    cd physics-engine
    npx supabase@2.121.0 start          # if it isn't running
    python3 eval/rls_tests.py

Exits non-zero on any failure, like ci_check.py.

WHY THIS IS SEPARATE FROM ci_check.py: ci_check runs offline with fakes, so it can run on
every pull request. Row-level security only means something when the real database
enforces it, so these tests talk to a real (local) Supabase through its REST API -- the
same path the browser and server.py use.

SAFETY: these tests create users, change roles and insert rows. They refuse to run unless
the Supabase URL is on this machine (127.0.0.1 / localhost), so they can never touch the
hosted project. Every user and row they create is deleted at the end, pass or fail.

Standard library only. Needs: the local stack running, Docker (to bootstrap the first admin
and clean up, as an operator would), and npx (to read the local URL and keys).
"""
import json
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlparse

RUN = uuid.uuid4().hex[:8]                 # unique per run, so runs never collide
EMAIL = "rlstest-{}-" + RUN + "@test.dev"
PASSWORD = "local-only-Passw0rd!"
TEXT_TAG = f"[rls-test {RUN}]"
DB_CONTAINER = "supabase_db_local-dev"
CLI = ["npx", "--yes", "supabase@2.121.0"]

failures = []


# ---------------------------------------------------------------- plumbing

def local_settings():
    out = subprocess.run(CLI + ["status", "-o", "json"], capture_output=True, text=True)
    try:
        s = json.loads(out.stdout)
    except ValueError:
        sys.exit("Couldn't read local Supabase status. Is it running? -> npx supabase@2.121.0 start")
    if urlparse(s["API_URL"]).hostname not in ("127.0.0.1", "localhost"):
        sys.exit(f"Refusing to run: {s['API_URL']} is not a local Supabase.")
    return s["API_URL"], s["PUBLISHABLE_KEY"], s["SECRET_KEY"]


URL, PUBLISHABLE, SECRET = local_settings()


def call(method, path, token=None, body=None, key=None, prefer=None):
    """Returns (status, parsed body). Never raises on an HTTP error code."""
    h = {"apikey": key or PUBLISHABLE, "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    if prefer:
        h["Prefer"] = prefer
    req = urllib.request.Request(URL + path, method=method, headers=h,
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw or b"null")
        except ValueError:
            return e.code, raw.decode(errors="replace")


def code(body):
    return body.get("code") if isinstance(body, dict) else None


def sql(query):
    """Operator access to the local database (bootstrap and cleanup only)."""
    out = subprocess.run(["docker", "exec", "-i", DB_CONTAINER, "psql", "-U", "postgres",
                          "-d", "postgres", "-tAc", query], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"SQL failed: {out.stderr.strip()}")
    return out.stdout.strip()


def sign_up(name):
    st, d = call("POST", "/auth/v1/signup", body={"email": EMAIL.format(name), "password": PASSWORD})
    if st != 200 or "access_token" not in d:
        sys.exit(f"Couldn't create test user {name}: {st} {d}")
    return d["access_token"], d["user"]["id"]


def check(label, got, want):
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:62} got {got!r}")
    if not ok:
        failures.append(label)


def role_of(user_id):
    return sql(f"select role from public.profiles where id = '{user_id}'")


SERVER = {"key": SECRET}                     # what server.py would use to write the log
LOG_ROW = {"problem_text": f"{TEXT_TAG} Two blocks hang from a pulley.", "verification": "verified"}


# ---------------------------------------------------------------- tests

def profiles_tests(alice, bob):
    print("\nprofiles")
    (a_tok, a_id), (b_tok, b_id) = alice, bob
    st, d = call("GET", "/rest/v1/profiles?select=id,role", a_tok)
    check("signup trigger gave alice exactly her own profile, role user",
          (st, [(r["id"], r["role"]) for r in d]), (200, [(a_id, "user")]))
    st, d = call("GET", f"/rest/v1/profiles?select=id&id=eq.{a_id}", b_tok)
    check("bob cannot read alice's profile (0 rows)", (st, len(d)), (200, 0))
    st, d = call("PATCH", f"/rest/v1/profiles?id=eq.{b_id}", b_tok, {"role": "admin"}, prefer="return=representation")
    check("bob promoting himself via the table changes 0 rows", (st, d), (200, []))
    check("  ...bob is still user", role_of(b_id), "user")
    st, d = call("PATCH", f"/rest/v1/profiles?id=eq.{a_id}", b_tok, {"role": "admin"}, prefer="return=representation")
    check("bob changing alice's role via the table changes 0 rows", (st, d), (200, []))
    st, d = call("POST", "/rest/v1/profiles", b_tok, {"id": str(uuid.uuid4()), "role": "admin"})
    check("bob inserting a fake profile is rejected (42501)", (st, code(d)), (403, "42501"))
    st, d = call("GET", "/rest/v1/profiles?select=id")
    check("no login: reads 0 profiles", (st, len(d)), (200, 0))


def topics_tests(alice):
    print("\ntopics")
    st, d = call("GET", "/rest/v1/topics?select=topic", alice[0])
    check("signed-in user reads all 17 topic pairs", (st, len(d)), (200, 17))
    st, d = call("GET", "/rest/v1/topics?select=topic")
    check("no login: reads 0 topics", (st, len(d)), (200, 0))
    st, d = call("POST", "/rest/v1/topics", alice[0], {"topic": "Fake", "subtopic": "Fake"})
    check("signed-in user cannot add topics (42501)", (st, code(d)), (403, "42501"))


def problems_log_tests(alice, admin):
    print("\nproblems_log")
    st, d = call("POST", "/rest/v1/problems_log", body={**LOG_ROW, "topic": "Mechanics", "subtopic": "Dynamics",
                                                        "tag_source": "engine_card"},
                 prefer="return=representation", **SERVER)
    check("server (secret key) writes a tagged row", st, 201)
    if st == 201:
        check("  ...created_at was rounded to the hour", d[0]["created_at"][14:19], "00:00")
    st, d = call("POST", "/rest/v1/problems_log", body={**LOG_ROW, "created_at": "2026-10-22T14:37:52Z"}, **SERVER)
    check("exact (non-hour) time is rejected (23514)", (st, code(d)), (400, "23514"))
    st, d = call("POST", "/rest/v1/problems_log", body={**LOG_ROW, "topic": "E&M", "subtopic": "Calorimetry",
                                                        "tag_source": "llm"}, **SERVER)
    check("invalid topic pair is rejected (23503)", (st, code(d)), (409, "23503"))
    st, d = call("POST", "/rest/v1/problems_log", body={**LOG_ROW, "topic": "Mechanics", "tag_source": "llm"}, **SERVER)
    check("topic without subtopic is rejected (23514)", (st, code(d)), (400, "23514"))
    st, d = call("POST", "/rest/v1/problems_log", body={**LOG_ROW, "redactions": -1}, **SERVER)
    check("negative redaction count is rejected (23514)", (st, code(d)), (400, "23514"))
    st, d = call("POST", "/rest/v1/problems_log", body=LOG_ROW, **SERVER)
    check("server writes an untagged row (tags come later)", st, 201)

    tagged = f"problem_text=like.{urllib.request.quote(TEXT_TAG)}*"
    st, d = call("GET", f"/rest/v1/problems_log?select=id&{tagged}", alice[0])
    check("normal user reads 0 rows of the log", (st, len(d)), (200, 0))
    st, d = call("POST", "/rest/v1/problems_log", alice[0], LOG_ROW)
    check("normal user cannot write the log (42501)", (st, code(d)), (403, "42501"))
    st, d = call("GET", f"/rest/v1/problems_log?select=id&{tagged}")
    check("no login: reads 0 rows of the log", (st, len(d)), (200, 0))
    st, d = call("GET", f"/rest/v1/problems_log?select=id&{tagged}", admin[0])
    check("admin reads this run's 2 rows", (st, len(d)), (200, 2))
    st, d = call("POST", "/rest/v1/problems_log", admin[0], LOG_ROW)
    check("even an admin cannot write the log from the browser (42501)", (st, code(d)), (403, "42501"))


def tagging_tests():
    """The tagging columns' rules, then the server's own writer (problem_log.py) end to end."""
    print("\nproblems_log tagging (server writer)")
    pair = {"topic": "Mechanics", "subtopic": "Dynamics"}
    st, d = call("POST", "/rest/v1/problems_log", body={**LOG_ROW, **pair}, **SERVER)
    check("topic without tag_source is rejected (23514)", (st, code(d)), (400, "23514"))
    st, d = call("POST", "/rest/v1/problems_log", body={**LOG_ROW, "tag_source": "llm"}, **SERVER)
    check("tag_source without topic is rejected (23514)", (st, code(d)), (400, "23514"))
    st, d = call("POST", "/rest/v1/problems_log", body={**LOG_ROW, **pair, "tag_source": "guess"}, **SERVER)
    check("unknown tag_source is rejected (23514)", (st, code(d)), (400, "23514"))

    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engine"))
    from problem_log import SupabaseLogStore, log_and_tag, LogError
    from pipeline import solve_physics_problem
    store = SupabaseLogStore(URL, SECRET)
    solution = solve_physics_problem("rls", "atwood", {"m1": 4, "m2": 6, "g": 9.8}, ["a", "T"],
                                     topic_hint="Mechanics")
    reply = json.dumps({"topic": "E&M", "subtopic": "Circuits", "grade_level": "high_school",
                        "difficulty": "easy", "confidence": 0.9})       # disagrees with the card
    query = f"{TEXT_TAG} I'm jane@uni.edu. Atwood machine, 4 kg and 6 kg: find a and T."
    outcome = log_and_tag(query, {"verification": "verified", "trace": solution}, store,
                          llm=lambda prompt, schema: (reply, "fake-model"))
    check("server writer: insert + tag succeeds", outcome, "tagged")
    st, d = call("GET", f"/rest/v1/problems_log?select=*&problem_text=like.*Atwood*"
                        f"&{'problem_text=like.' + urllib.request.quote(TEXT_TAG) + '*'}", **SERVER)
    row = d[0] if st == 200 and d else {}
    check("  ...stored text is redacted, count 1", ("jane@" in row.get("problem_text", ""), row.get("redactions")),
          (False, 1))
    check("  ...card label kept, source engine_card, card recorded",
          (row.get("topic"), row.get("subtopic"), row.get("tag_source"), row.get("matched_card")),
          ("Mechanics", "Dynamics", "engine_card", "MECH-DYN-ATWOOD"))
    check("  ...model disagreed -> needs_review with reason",
          (row.get("needs_review"), row.get("review_reason")), (True, "model said E&M / Circuits"))
    try:
        store.insert({**LOG_ROW, "redactions": -1})
        check("server writer: invalid row raises LogError", "accepted", "LogError")
    except LogError as e:
        check("server writer: invalid row raises LogError without row contents",
              ("23514" in str(e), "pulley" in str(e)), (True, False))


def role_tests(alice, bob, admin):
    print("\nset_user_role / admin_list_users")
    (a_tok, a_id), (b_tok, b_id), (adm_tok, adm_id) = alice, bob, admin

    def set_role(tok, target, role):
        st, d = call("POST", "/rest/v1/rpc/set_user_role", tok, {"target_user": target, "new_role": role})
        return st, code(d)

    check("user cannot promote another user (42501)", set_role(b_tok, a_id, "admin"), (403, "42501"))
    check("user cannot promote himself (42501)", set_role(b_tok, b_id, "admin"), (403, "42501"))
    check("no login cannot call it", set_role(None, a_id, "admin")[0] in (401, 403), True)
    check("admin promotes alice (204)", set_role(adm_tok, a_id, "admin")[0], 204)
    check("  ...alice is now admin", role_of(a_id), "admin")
    check("invalid role name is rejected (400)", set_role(adm_tok, b_id, "superadmin")[0], 400)
    check("unknown user is rejected (22023)", set_role(adm_tok, str(uuid.uuid4()), "admin"), (400, "22023"))

    st, d = call("POST", "/rest/v1/rpc/admin_list_users", adm_tok, {})
    mine = sorted((u["email"], u["role"]) for u in d if RUN in u["email"]) if st == 200 else d
    check("admin lists this run's users with roles", (st, mine),
          (200, sorted([(EMAIL.format("alice"), "admin"), (EMAIL.format("bob"), "user"),
                        (EMAIL.format("admin"), "admin")])))
    st, d = call("POST", "/rest/v1/rpc/admin_list_users", b_tok, {})
    check("user cannot list users (42501)", (st, code(d)), (403, "42501"))
    st, d = call("POST", "/rest/v1/rpc/admin_list_users", None, {})
    check("no login cannot list users", st in (401, 403), True)

    # Last-admin rule: make this run's two admins the ONLY admins, then demote down to one.
    saved = sql("select coalesce(string_agg(id::text, ','), '') from public.profiles where role = 'admin' "
                f"and id not in ('{a_id}', '{adm_id}')")
    if saved:
        sql(f"update public.profiles set role = 'user' where id in ('{saved.replace(',', chr(39) + ',' + chr(39))}')")
    try:
        check("admin demotes alice while another admin remains (204)", set_role(adm_tok, a_id, "user")[0], 204)
        check("the last admin cannot demote himself (P0001)", set_role(adm_tok, adm_id, "user"), (400, "P0001"))
        check("  ...he is still admin", role_of(adm_id), "admin")
    finally:
        if saved:  # give back admin to anyone who had it before the test
            sql(f"update public.profiles set role = 'admin' where id in ('{saved.replace(',', chr(39) + ',' + chr(39))}')")


# ---------------------------------------------------------------- main

if __name__ == "__main__":
    print(f"RLS tests against {URL} (run {RUN})")
    try:
        alice, bob, admin = sign_up("alice"), sign_up("bob"), sign_up("admin")
        sql(f"update public.profiles set role = 'admin' where id = '{admin[1]}'")   # operator bootstrap
        profiles_tests(alice, bob)
        topics_tests(alice)
        problems_log_tests(alice, admin)
        tagging_tests()
        role_tests(alice, bob, admin)
    finally:
        sql(f"delete from public.problems_log where problem_text like '{TEXT_TAG}%'")
        sql(f"delete from auth.users where email like 'rlstest-%-{RUN}@test.dev'")    # cascades to profiles
        print("\ncleaned up this run's users and rows")

    print()
    if failures:
        print(f"FAILED: {len(failures)} -> {failures}")
        sys.exit(1)
    print("All RLS tests passed.")
