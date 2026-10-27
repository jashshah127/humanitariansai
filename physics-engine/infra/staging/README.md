# Recreating the staging service

The service is defined in `render.yaml` in this folder. It holds no secret values.

1. Render dashboard: New > Blueprint > repo `jashshah127/humanitariansai`.
2. Branch `feature-harsh` (change to `main` after the Supabase work is merged).
3. Blueprint Path: `physics-engine/infra/staging/render.yaml`.
4. Choose "Create all as new services" (or "Associate existing services" to adopt a running one).
5. Enter the six secret values when prompted:
   - `GEMINI_API_KEY`: a key from aistudio.google.com/apikey
   - `JWT_SECRET`: a new random string, for example from
     `python -c "import secrets; print(secrets.token_hex(32))"`
   - `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`: from the Supabase project's API settings
   - `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`: the same two values again.
     The frontend reads these at build time, so each environment needs its own.
6. Verify: `/health` returns status ok, provider GeminiLLM, frontend react.
   Then sign in and solve the example problem.
7. Add the staging address to the Supabase redirect URLs, or sign-up and
   password-reset emails will not work.

Notes
- Auto-deploy is set to "after CI checks pass". CI must run on pushes to the
  tracked branch; the workflow has a push trigger for `main` and `feature-harsh`.
- Free instances sleep after 15 minutes idle (about a minute to wake) and share
  750 free instance hours per month across the workspace.