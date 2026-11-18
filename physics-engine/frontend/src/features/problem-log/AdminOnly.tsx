import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router";
import type { ProblemLogStore } from "../../api/problemLog.ts";
import styles from "./problemLog.module.css";

/**
 * Shows its children only to admins. The database refuses non-admins anyway; this is so a
 * non-admin sees a clear message instead of an empty page.
 */
export function AdminOnly({ store, children }: { store: ProblemLogStore; children: ReactNode }) {
  const [access, setAccess] = useState<"checking" | "admin" | "denied" | "error">("checking");

  useEffect(() => {
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
  }, [store]);

  if (access === "admin") return <>{children}</>;
  return (
    <main className={styles.page}>
      {access === "checking" && <p className={styles.status}>Checking access…</p>}
      {access === "denied" && (
        <>
          <h1 className={styles.title}>Admins only</h1>
          <p className={styles.status}>
            The problem history is for admins. <Link to="/app">Back to the workspace</Link>.
          </p>
        </>
      )}
      {access === "error" && (
        <p role="alert" className={styles.status}>
          Your access couldn’t be checked. Reload the page to try again.
        </p>
      )}
    </main>
  );
}