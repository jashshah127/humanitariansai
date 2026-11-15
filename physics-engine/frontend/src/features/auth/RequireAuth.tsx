import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { useAuth } from "./AuthContext.ts";
import styles from "./auth.module.css";

/** Shows its children only to a signed-in user; everyone else goes to /login. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { session, loading, configured } = useAuth();
  const location = useLocation();

  if (!configured) {
    return (
      <main className={styles.page}>
        <h1 className={styles.title}>Sign-in isn’t set up</h1>
        <p className={styles.lead}>
          This build has no VITE_SUPABASE_URL or VITE_SUPABASE_PUBLISHABLE_KEY.
        </p>
      </main>
    );
  }
  if (loading) {
    return (
      <main className={styles.page}>
        <p className={styles.note}>Checking your sign-in…</p>
      </main>
    );
  }
  if (!session) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }
  return <>{children}</>;
}
