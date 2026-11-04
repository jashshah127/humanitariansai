# Auth architecture

How sign-up, sign-in, roles and data access work in the Physics Engine: which piece does what,
how a request is checked, and where the rules are enforced.

**Status (2026-11-03):** backend on branch `feature-shailly`; frontend sign-in pages on `feature-atharva`.
Neither is merged into `main` yet. The database migrations are applied to the hosted Supabase project.

No keys, passwords or project URLs appear here — only the **names** of the settings that hold them.

---

## 1. The pieces

| Piece | Role | Code |
|---|---|---|
| **Supabase Auth** | Accounts, passwords, sessions, email confirmation and password reset. The app never stores passwords | Hosted by Supabase |
| **Browser (React)** | Signs users up and in **directly with Supabase**, keeps the session, sends the access token to our server | `frontend/src/api/supabase.ts`, `frontend/src/features/auth/` |
| **`server.py`** | Checks the token on `/solve`, `/parse`, `/grade`, `/me`. It never issues tokens and never sees passwords | `server.py`, `engine/supabase_auth.py`, `engine/jwt_auth.py` |
| **Postgres (Supabase)** | Holds each user's role and the app's tables; **row-level security (RLS)** decides who can read or write each row | `supabase/migrations/` |

```
 Browser ──sign up / sign in──▶ Supabase Auth ──(trigger)──▶ profiles row (role = user)
    │                                │
    │  Authorization: Bearer <access token>
    ▼                                │
 server.py ──"is this session live?"─┘  GET /auth/v1/user
    │
    └──▶ /solve, /parse, /grade, /me
```

---

## 2. Signing up and signing in (browser ↔ Supabase)

The browser uses `@supabase/supabase-js`, configured with `VITE_SUPABASE_URL` and
`VITE_SUPABASE_PUBLISHABLE_KEY`. If either is missing, the app shows "Sign-in isn't set up".

| Page | What happens |
|---|---|
| `/signup` | `signUp(email, password)`. If email confirmation is on, the user must click the emailed link, which returns them to `/login` |
| `/login` | `signInWithPassword(email, password)` |
| `/reset-password` | Requests a reset email, then sets a new password when the user returns from the link |
| `/app` | Wrapped in `RequireAuth`: anyone not signed in is sent to `/login` |

**Session:** supabase-js keeps the session (access token + refresh token) in the browser's **localStorage** and
refreshes the access token automatically before it expires (tokens last **60 minutes**). No cookies are used.

**Creating the profile:** when Supabase adds a row to `auth.users`, the database trigger `on_auth_user_created`
inserts a matching `public.profiles` row with role **`user`**. No account exists without a profile.

---

## 3. Calling our server

The frontend sends the current access token on every API call:

```
Authorization: Bearer <access token>
```

### 3.1 How `server.py` checks a token

`server.py` accepts two kinds of token:

1. **Operator-minted token** (HS256, signed with `JWT_SECRET`, created with `mint_token.py`) — kept for CI, demos
   and older developer setups; checked first because it needs no network call. It carries no user identity.
2. **Supabase session token** — checked by `engine/supabase_auth.py`, which **asks Supabase**
   (`GET <SUPABASE_URL>/auth/v1/user`) whether the session is still live.

Order of checks:

```
no / malformed Authorization header  → 401
minted token valid                   → allowed
Supabase not configured              → 401
Supabase confirms the session        → allowed   (caller remembered on handler.caller)
Supabase rejects the token           → 401       (expired, forged, signed out)
Supabase can't be reached            → 503       ("Sign-in can't be checked right now")
```

**Why ask Supabase instead of checking the signature locally?**

| | Ask Supabase (**chosen**) | Verify locally (cached public keys) |
|---|---|---|
| Dependencies | Standard library only | A JWT library with elliptic-curve support |
| Sign-out | Takes effect **immediately** | Token keeps working until it expires |
| Signing algorithm | Doesn't matter (hosted project: ES256; local CLI stack: HS256) | Must handle each |
| Cost | One network call per request | Fast after the first key download |

**401 vs 503:** a refused token is the caller's problem (401). Supabase being unreachable is ours (503) — telling a
signed-in user their session is invalid would be wrong.

### 3.2 `GET /me`

Token-gated, not rate-limited. Returns who the caller is and their role, so the frontend can decide what to show:

```json
{"kind": "supabase", "id": "<uuid>", "email": "<email>", "role": "user" | "admin"}
{"kind": "minted", "sub": "<subject>", "role": null}
```

The role is read from the caller's **own** `profiles` row **using the caller's own token**, so RLS applies and the
server needs no secret key for it. If the lookup fails, `/me` answers 503 rather than guessing.

---

## 4. Roles

| Object | Purpose |
|---|---|
| `public.app_role` | Enum: `user`, `admin`. The database rejects any other value |
| `public.profiles` | One row per account (same id as `auth.users`), holding `role` (default `user`) |
| `public.is_admin()` | True if the caller's profile role is `admin`. Used by admin-only rules |
| `public.set_user_role(target_user, new_role)` | **Admins only.** Grants or removes the admin role |
| `public.admin_list_users()` | **Admins only.** Every user's id, email, role and sign-up time |

Rules enforced inside the database, so no client can bypass them:

- Users **cannot change their own role**: `profiles` has no update policy, and `set_user_role` checks `is_admin()` first.
- **The last admin cannot be demoted**, so the app is never left without an admin. Admin rows are locked before
  counting, so two admins demoting each other at the same moment cannot both succeed.
- `set_user_role` and `admin_list_users` are **not callable by anonymous visitors**.

**The first admin** is created by an operator with one SQL statement in the Supabase SQL Editor (nobody is an admin
yet to grant it):

```sql
update public.profiles set role = 'admin'
where id = (select id from auth.users where email = '<their email>');
```

After that, admins promote others through the API:

```js
await supabase.rpc("set_user_role", { target_user: userId, new_role: "admin" });   // or "user"
await supabase.rpc("admin_list_users");
```

| Error | Meaning |
|---|---|
| `42501` (HTTP 403) | Caller is not an admin |
| `P0001` (HTTP 400) | Would remove the last admin |
| `22023` (HTTP 400) | No such user |

---

## 5. Data access and row-level security

Every table has RLS **on**. With RLS on and no matching policy, access is denied by default.

| Table | Read | Write |
|---|---|---|
| `profiles` | Own row only | Only via the signup trigger and `set_user_role` |
| `topics` | Any signed-in user | Nobody through the API (seeded by migration) |
| `problems_log` | **Admins only** | **Server only** (secret key). No browser can write, not even an admin |

`problems_log` is **de-identified**: no user id, no session id, timestamps rounded to the hour.

**Behaviour to remember:** a read or update blocked by RLS does **not** return an error — it succeeds with fewer or
zero rows. Only a blocked insert returns 403. Code and tests must check what changed, not only the status code.

---

## 6. Configuration

**Server (`server.py`)** — environment variables:

| Variable | Needed for | Secret? |
|---|---|---|
| `SUPABASE_URL` | Supabase sign-in | No |
| `SUPABASE_PUBLISHABLE_KEY` | Supabase sign-in (sent as `apikey`) | No — designed to be public |
| `JWT_SECRET` | Operator-minted tokens | **Yes** |

The startup line reports what is active, e.g. `Auth: minted tokens + Supabase sign-in`.

**Frontend build:** `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`.

**Never** put the Supabase **secret** key in the frontend or in this repo: it bypasses all RLS. Only the server may
hold it (needed later for writing `problems_log`).

**Supabase project settings** (dashboard → Authentication):

| Setting | Current choice |
|---|---|
| Sign-ups | Open |
| Email confirmation | On (the built-in email sender is rate-limited; testing accounts can be created in the dashboard with *Auto Confirm User*) |
| Site URL / redirect URLs | Local frontend (`http://localhost:5173`, `http://127.0.0.1:5173`) and the deployed site; email links only return to listed URLs |

---

## 7. Environments and schema changes

| Environment | Used for |
|---|---|
| **Local** — `npx supabase@2.121.0 start` in `physics-engine/` (Docker) | Development and tests. Email confirmation is off locally (`supabase/config.toml`) |
| **Hosted** Supabase project | Shared testing |

Schema changes are migration files in `supabase/migrations/`, applied in order:

1. `20261015194448_initial_schema.sql` — `app_role`, `profiles`, signup trigger
2. `20261022164924_problems_log.sql` — `topics`, `is_admin()`, `problems_log`
3. `20261103224949_role_assignment.sql` — `set_user_role()`, `admin_list_users()`

Locally, `npx supabase@2.121.0 db reset` rebuilds the database from these files. For the hosted project:
`db push --dry-run` first, then `db push`. Add a new migration for every change; never edit one that has been applied
to a shared database.

---

## 8. Tests

| Suite | Runs | Covers |
|---|---|---|
| `eval/ci_check.py` → *Auth invariants* | Offline, in CI on every pull request | Supabase reply mapping; every server auth path (incl. "a minted token never calls Supabase"); `/me` roles |
| `eval/rls_tests.py` | Against the **local** Supabase (`python3 eval/rls_tests.py`) | 35 checks across `profiles`, `topics`, `problems_log`, `set_user_role`, `admin_list_users`, including one user trying to read or change another's data |

`rls_tests.py` refuses to run against anything but a local Supabase, and deletes the users and rows it creates.

---

## 9. Security notes

- **Sign-out:** after sign-out, Supabase Auth rejects the old token at once (so `server.py` does too), but the
  Supabase **REST API** keeps accepting it until it expires (up to 60 minutes). The refresh token stops working
  immediately.
- **localStorage:** any script running on the page can read the session. Keep the frontend free of injected HTML.
- **Rate limiting runs before authentication** on `/solve`, `/parse` and `/grade` (when `/grade` has to call the AI),
  so unauthenticated requests still use the shared AI quota.
- **Local Supabase** listens on the network and its dashboard has no login: stop it when not in use; test data only.
- **Student data:** no student-identified data should be stored until Q6 (data processing agreement / IRB) is settled.

---

## 10. Known limitations and open items

| Item | Notes |
|---|---|
| **Page addresses return 404 on the deployed server** | `server.py` serves only files that exist in `frontend/dist/`, so opening `/login`, `/signup` or `/reset-password` directly — including from an email link — gives 404. Locally, Vite handles it. Fix: serve `index.html` for unknown non-API paths |
| Operator-minted tokens are still accepted | Kept for the transition; can be retired once everyone signs in through Supabase |
| No in-app admin page yet | The database functions exist; the UI is still to be built |
| Production email | Needs a real email provider before opening sign-ups widely |
| Not merged into `main` | Backend on `feature-shailly`, frontend on `feature-atharva` |
