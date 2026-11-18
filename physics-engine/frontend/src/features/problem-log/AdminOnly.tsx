import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router";
import type { ProblemLogStore } from "../../api/problemLog.ts";
import styles from "./problemLog.module.css";
import { useAuth } from "../auth/AuthContext.ts";
/**
 * Shows its children only to admins. The database refuses non-admins anyway; this is so a
 * non-admin sees a clear message instead of an empty page.
 */
export function AdminOnly({ store, children }: { store: ProblemLogStore; children: ReactNode }) {
  const { isGuest } = useAuth();
  const [access, setAccess] = useState<"checking" | "admin" | "denied" | "error">("checking");

  useEffect(() => {
if (isGuest) return;
    let live = true;
    store.isAdmin().then(
      (ok) => {
        if (live) setAccess(ok ? "admin" : "denied");
      },
      (e: unknown) => {
        console.error("[problem log] admin check failed", e);
        if (live) setAccess("error");
      },
    );
    return () => {
      live = false;
    };
  }, [store, isGuest]);
  const shown = isGuest ? "denied" : access;
  if (shown === "admin") return <>{children}</>;
  return (
    <main className={styles.page}>
      {shown === "checking" && <p className={styles.status}>Checking access…</p>}
      {shown === "denied" && (
        <>
          <h1 className={styles.title}>Admins only</h1>
          <p className={styles.status}>
            The problem history is for admins. <Link to="/app">Back to the workspace</Link>.
          </p>
        </>
      )}
      {shown === "error" && (
        <p role="alert" className={styles.status}>
          Your access couldn’t be checked. Reload the page to try again.
        </p>
      )}
    </main>
  );
}

