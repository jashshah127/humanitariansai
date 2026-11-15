import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { arrivedFromRecoveryLink, linkError, supabase } from "../../api/supabase.ts";
import { AuthContext, signedOut } from "./AuthContext.ts";
import type { AuthValue } from "./AuthContext.ts";
import { friendly } from "./authErrors.ts";

/** Where email links send the user back to. Each must be in Supabase's redirect list. */
function backTo(path: string): string {
  return `${window.location.origin}${path}`;
}

/** Supabase returns { error } instead of throwing; turn it into a thrown, reworded Error. */
async function check<T extends { error: { message: string } | null }>(p: Promise<T>): Promise<T> {
  const result = await p;
  if (result.error) throw new Error(friendly(result.error.message));
  return result;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(supabase !== null);

  useEffect(() => {
    if (!supabase) return;
    // Fires once at start with the saved session, then on sign-in, sign-out and
    // the hourly token refresh, so `token` is always the current one.
    const { data } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
      setLoading(false);
    });
    return () => data.subscription.unsubscribe();
  }, []);

  const value = useMemo<AuthValue>(() => {
    const client = supabase;
    if (!client) return signedOut;
    return {
      session,
      token: session?.access_token ?? "",
      loading,
      configured: true,
      recoveryLink: arrivedFromRecoveryLink,
      linkError,
      async signIn(email, password) {
        await check(client.auth.signInWithPassword({ email, password }));
      },
      async signUp(email, password) {
        const r = await check(
          client.auth.signUp({ email, password, options: { emailRedirectTo: backTo("/login") } }),
        );
        return { needsConfirmation: r.data.session === null };
      },
      async signOut() {
        await client.auth.signOut();
        setSession(null); // even if the network call failed, this tab is signed out
      },
      async requestReset(email) {
        await check(
          client.auth.resetPasswordForEmail(email, { redirectTo: backTo("/reset-password") }),
        );
      },
      async updatePassword(password) {
        await check(client.auth.updateUser({ password }));
      },
    };
  }, [session, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
