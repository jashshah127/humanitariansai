import { Button } from "../../design/components/Button.tsx";
import styles from "./guest.module.css";

/** Where a guest can go to keep solving. Both need the guest session ended first. */
export type LeaveTo = "/signup" | "/login";

/**
 * Shown above the workspace while signed in as a guest. `remaining` comes from the
 * server (guest_remaining on each /solve or /parse reply); null until the first reply.
 * No "x of 3": the total is set on the server (GUEST_PROBLEM_LIMIT), and a number here
 * could disagree with it.
 */
export function GuestBanner({
  remaining,
  onLeave,
}: {
  remaining: number | null;
  onLeave: (to: LeaveTo) => void;
}) {
  const text =
    remaining === null
      ? "You’re trying the engine as a guest, with a few free problems."
      : remaining === 0
        ? "That was your last guest problem."
        : `${remaining} guest ${remaining === 1 ? "problem" : "problems"} left.`;
  return (
    <div className={styles.banner} role="status">
      <p className={styles.text}>
        {text} Create an account to keep solving.
      </p>
      <Button variant="secondary" size="sm" onClick={() => onLeave("/signup")}>
        Create an account
      </Button>
    </div>
  );
}

/** Replaces the error box when the server refuses a guest (403 guest_limit / daily_limit). */
export function GuestLimit({ message, onLeave }: { message: string; onLeave: (to: LeaveTo) => void }) {
  return (
    <div className={styles.limit} role="alert">
      <p className={styles.text}>{message}</p>
      <div className={styles.actions}>
        <Button onClick={() => onLeave("/signup")}>Create an account</Button>
        <Button variant="secondary" onClick={() => onLeave("/login")}>
          Sign in
        </Button>
      </div>
    </div>
  );
}