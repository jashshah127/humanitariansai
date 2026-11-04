# API contract: sign-in and the protected endpoints

What the frontend calls, what it sends, and what comes back, including every error it should handle.
For *why* it works this way (token checks, roles, RLS), see [auth-architecture.md](auth-architecture.md).

**Status (2026-11-03):** matches `server.py` on branch `feature-shailly`. No keys or project URLs appear here.

---

## 1. Two services, two jobs

| Job | Who the browser talks to | How |
|---|---|---|
| Sign up, sign in, sign out, reset password, refresh the session | **Supabase Auth**, directly | `@supabase/supabase-js` (`frontend/src/api/supabase.ts`) |
| Solve, parse, grade, "who am I" | **`server.py`** | `fetch` with `Authorization: Bearer <access token>` |

`server.py` never sees a password and never issues a token. It only checks the token the browser sends.

---

## 2. Sign-in calls (browser → Supabase)

| Action | Call | On success |
|---|---|---|
| Sign up | `supabase.auth.signUp({ email, password, options: { emailRedirectTo } })` | Hosted project: email confirmation is **on**, so there is no session until the user clicks the link. Local stack: confirmation is off, session at once |
| Sign in | `supabase.auth.signInWithPassword({ email, password })` | `data.session` holds `access_token` and `refresh_token` |
| Sign out | `supabase.auth.signOut()` | `server.py` rejects the old token immediately (401) |
| Reset password | `supabase.auth.resetPasswordForEmail(email, { redirectTo })`, then `supabase.auth.updateUser({ password })` on return | — |
| Current token | `(await supabase.auth.getSession()).data.session?.access_token` | Read it **per request**: supabase-js refreshes it before it expires (60 min) |

`emailRedirectTo` and `redirectTo` must be in the project's allowed redirect URLs (local frontend and deployed site).

**Errors worth a specific message** (`error.code` from supabase-js):

| Code | Meaning | Suggested message |
|---|---|---|
| `invalid_credentials` | Wrong email or password | "Email or password is incorrect." |
| `email_not_confirmed` | Signed up but hasn't clicked the link | "Check your inbox to confirm your email." |
| `weak_password` | Password fails the project's rules | Show `error.message` |
| `over_email_send_rate_limit` | Built-in email sender limit reached | "Too many emails sent. Try again later." |

With email confirmation on, signing up with an email that **already has an account** may not return an error. Supabase
avoids revealing which emails are registered. Show the same "check your inbox" message either way.

---

## 3. Calling `server.py`

### 3.1 Every protected call

```
POST /solve                      (same for /parse, /grade; GET for /me)
Content-Type: application/json
Authorization: Bearer <access_token from the current Supabase session>
```

**Same origin only.** The server answers no `OPTIONS` (CORS preflight) requests, so a browser call from another
origin that carries `Authorization` will fail. This works because:
- **Production:** `server.py` serves the built frontend itself (`frontend/dist`), so it's one origin.
- **Development:** Vite on `:5173` forwards API paths to `server.py` on `:8000` (`frontend/vite.config.ts` → `server.proxy`).
  **Every endpoint must be in that list.** `/me` currently isn't, so add `"/me": api`.

### 3.2 Endpoints

| Method + path | Token | Body | Returns |
|---|---|---|---|
| `GET /health` | No | — | `{"status": "ok", ...}` |
| `GET /cards` | No | — | The formula cards (`id`, `name`, `topic`, `subtopic`, `solves_for`, `applies_when`) |
| `GET /stats` | No | — | Route split and latency summary |
| `GET /me` | **Yes** | — | Who is calling and their role (below) |
| `POST /solve` | **Yes** | `{"query": str, "session_id": str, "render": "solve" \| "tutor"}` | The solve result (`frontend/src/api/types.ts`, `engine/physics_mode_api.json`) |
| `POST /parse` | **Yes** | `{"query": str}` | `{"gradable": bool, "reason"?, "unknowns", "given", "parsed"}` |
| `POST /grade` | **Yes** | `{"query": str, "parsed": <from /parse>, "student_answer": {name: number}}` | The grade result |

`session_id` groups usage statistics for one browser tab. It is **not** a student identifier. Keep it a random id.

### 3.3 `GET /me`

```json
{"kind": "supabase", "id": "<uuid>", "email": "<email>", "role": "user"}
{"kind": "supabase", "id": "<uuid>", "email": "<email>", "role": "admin"}
{"kind": "minted",   "sub": "<subject>", "role": null}
```

Call it after sign-in (and after a page reload with a saved session) to decide whether to show admin features.
`role` is read from the database on every call, so a promotion or demotion shows up on the next `/me`.
**Use the role for what to show, never as protection.** Admin data is protected by the database (RLS), whatever the UI shows.

### 3.4 Status codes

| Status | When | Body | What the UI should do |
|---|---|---|---|
| `200` | Success | Endpoint result | — |
| `200` with `"route": "error"` | `/solve` only: the engine failed (e.g. the AI provider is down) | `verification: "unverified"`, `explanation` = a student-safe message | Show it as an unverified answer with the message |
| `400` | Malformed body (e.g. `student_answer` not numbers) | `{"error": "<what is wrong>"}` | A bug in the request; show a generic message |
| `401` | No token, expired, forged or signed out | `{"error": "unauthorized: ..."}` | Send the user to `/login` |
| `404` | Unknown path | `{"error": "not found"}` | — |
| `429` | The shared AI-call limit (8 per minute, for everyone) is used up | `{"error", "retry_after_seconds"}` + `Retry-After` header | "Busy, try again in N seconds" |
| `503` | **Sign-in can't be checked** (Supabase unreachable), **role lookup failed** (`/me`), or `/parse`/`/grade` engine error | `{"error": "<student-safe message>"}` | **Show `error` as-is** and offer a retry. Not a sign-out: the session may be fine |

Order of checks on `/solve` and `/parse`: **rate limit → token → work**. So a request with a bad token can still get a
429 before it gets a 401.

---

## 4. What happens to a solved problem

When the server has `SUPABASE_SECRET_KEY` set, each `/solve` is also stored in `problems_log` for the admin dashboard:
- The text is cleaned first: emails, phone numbers, links and ID numbers are replaced. **Names are not removed.**
- There is no user id and no session id, and the time is rounded to the hour.
- Tagging (topic, subtopic, grade, difficulty) happens in the background.

The answer is never delayed by this. No response field changes. Until the data-governance question (Q6) is settled,
the UI should tell students not to include personal details in problems.

---

## 5. Frontend checklist

- [ ] Add `"/me": api` to the Vite proxy (`frontend/vite.config.ts`).
- [ ] Read the access token from `supabase.auth.getSession()` for each request, not once at sign-in.
- [ ] On `401`: clear any saved state and redirect to `/login`.
- [ ] On `503`: show the server's `error` text with a retry button. Don't sign the user out.
- [ ] After sign-in: call `GET /me` and show admin features only when `role === "admin"`.
- [ ] Optional: a short note near the problem box: "Don't include personal details."
- [ ] Known server gap: opening `/login`, `/signup` or `/reset-password` directly on the deployed server returns 404
      (no fallback to `index.html`). This also breaks email links. Fix belongs in `server.py` / `engine/static_files.py`.
