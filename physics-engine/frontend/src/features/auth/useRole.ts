import { useEffect, useRef, useState } from "react";
import { isAbort } from "../../api/client.ts";
import { fetchMe } from "../../api/me.ts";

export type Role = "user" | "admin";
/** idle: signed out. failed: /me didn't answer, so the user is treated as not an admin. */
export type RoleStatus = "idle" | "loading" | "ready" | "failed";

interface Fetched {
  forUser: string;
  role: Role | null;
  status: "ready" | "failed";
}

/**
 * Asks GET /me for the signed-in user's role, once per user.
 *
 * Keyed on the user's id, not the token: Supabase refreshes the token every hour, and
 * asking again each time would only cost two Supabase calls for the same answer.
 *
 * The role is ONLY for showing or hiding things. The real protection is on the database
 * side (admin_list_users / set_user_role refuse non-admins), so a wrong role here can
 * never give anyone admin powers.
 */
export function useRole(
  userId: string | null,
  token: string,
): { role: Role | null; roleStatus: RoleStatus } {
  const [fetched, setFetched] = useState<Fetched | null>(null);
  // Which user we already asked about. A ref, so changing it doesn't re-render.
  const askedFor = useRef<string | null>(null);

  useEffect(() => {
    if (!userId || !token) {
      askedFor.current = null; // signed out: ask again on the next sign-in
      return;
    }
    if (askedFor.current === userId) return; // same user, new token: keep the role
    askedFor.current = userId;

    const controller = new AbortController();
    let done = false;
    fetchMe(token, controller.signal)
      .then((me) => {
        done = true;
        // Anything other than "admin" (including no role) means not an admin.
        setFetched({
          forUser: userId,
          role: me.role === "admin" ? "admin" : "user",
          status: "ready",
        });
      })
      .catch((e: unknown) => {
        if (isAbort(e)) return;
        done = true;
        setFetched({ forUser: userId, role: null, status: "failed" });
      });

    return () => {
      // Stopped before an answer came back (StrictMode's double run in dev, a new
      // token mid-request, sign-out): forget we asked, so the next run asks again.
      if (!done) {
        controller.abort();
        askedFor.current = null;
      }
    };
  }, [userId, token]);

  if (!userId) return { role: null, roleStatus: "idle" };
  // A result for an earlier user, or none yet: still loading for this one.
  if (!fetched || fetched.forUser !== userId) return { role: null, roleStatus: "loading" };
  return { role: fetched.role, roleStatus: fetched.status };
}
