import { useEffect, useState } from "react";
import type { ApiError } from "../../api/client.ts";
import { Button } from "../../design/components/Button.tsx";
import styles from "./workspace.module.css";

interface Props {
  error: ApiError;
  /** Sends the same problem again. Not offered for auth errors: a retry can't fix a bad token. */
  onRetry: () => void;
}

export function ErrorState({ error, onRetry }: Props) {
  const [wait, setWait] = useState(error.kind === "rate" ? (error.retryAfter ?? 0) : 0);

  // Count down so the student knows when retrying will work.
  useEffect(() => {
    if (wait <= 0) return;
    const t = setTimeout(() => setWait((w) => w - 1), 1000);
    return () => clearTimeout(t);
  }, [wait]);

  const canRetry = error.kind !== "auth";

  return (
    <div className={styles.error} role="alert">
      <p className={styles.errorText}>
        <ErrorIcon />
        <span>
          {error.message}
          {error.kind === "rate" && wait > 0 && ` You can try again in ${wait} seconds.`}
        </span>
      </p>
      {canRetry && (
        <Button type="button" onClick={onRetry} disabled={wait > 0}>
          Try again
        </Button>
      )}
    </div>
  );
}
function ErrorIcon() {
  return (
    <svg
      className={styles.errorIcon}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      aria-hidden="true"
      focusable="false"
    >
      <circle cx="8" cy="8" r="6.5" />
      <path d="M8 4.75v3.75" />
      <circle cx="8" cy="11" r="0.6" fill="currentColor" stroke="none" />
    </svg>
  );
}
