import { useEffect, useState } from "react";
import { problemLogStore } from "../../api/problemLog.ts";
import type { ProblemLogStore } from "../../api/problemLog.ts";
import { ButtonLink } from "../../design/components/ButtonLink.tsx";
import { useAuth } from "../auth/AuthContext.ts";

/**
 * The "Problem logs" button in the workspace header. Shown to admins only: a non-admin
 * would only reach the "Admins only" page. Hidden while checking and if the check fails --
 * the page itself still refuses non-admins, so hiding is never the protection.
 */
export function ProblemLogLink({ store = problemLogStore }: { store?: ProblemLogStore }) {
    const { session, isGuest } = useAuth();
  const userId = session?.user.id ?? null;
  // The answer is kept with the user it was for, so after switching accounts the old
  // answer is never shown while the new one is being checked.
  const [checked, setChecked] = useState<{ user: string | null; admin: boolean } | null>(null);

  useEffect(() => {
          if (isGuest) return; // guests are never admins: don't even ask
    let live = true;
    store.isAdmin().then(
      (admin) => {
        if (live) setChecked({ user: userId, admin });
      },
      (e: unknown) => {
        console.warn("[problem log] admin check failed; hiding the button", e);
        if (live) setChecked({ user: userId, admin: false });
      },
    );
    return () => {
      live = false;
    };
  }, [store, userId, isGuest]);

  if (isGuest || !checked || checked.user !== userId || !checked.admin) return null;
  return (
    <ButtonLink to="/app/history" variant="secondary" size="sm">
      Problem logs
    </ButtonLink>
  );
}