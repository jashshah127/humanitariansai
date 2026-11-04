// The one Supabase client for the whole app. Sign-in happens in the browser;
// server.py only checks the token it is sent (engine/supabase_auth.py).
import { createClient } from "@supabase/supabase-js";
import type { SupabaseClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL;
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

// Read the link details BEFORE the client is created: the client signs in from the
// "#access_token=..." part of the URL and then removes it.
function readHash(): URLSearchParams {
  try {
    return new URLSearchParams(window.location.hash.slice(1));
  } catch {
    return new URLSearchParams();
  }
}
const hash = readHash();

/** True when this page load came from a "reset your password" email link. */
export const arrivedFromRecoveryLink = hash.get("type") === "recovery";

/** Set when an email link was refused (expired or already used). */
export const linkError: string | null = hash.get("error_description");

/** null when the build has no Supabase settings; the app then says sign-in isn't set up. */
export const supabase: SupabaseClient | null =
  url && key
    ? createClient(url, key, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
      })
    : null;
