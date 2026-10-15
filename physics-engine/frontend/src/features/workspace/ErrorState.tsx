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
        {error.message}
        {error.kind === "rate" && wait > 0 && ` You can try again in ${wait} seconds.`}
      </p>
      {canRetry && (
        <Button type="button" onClick={onRetry} disabled={wait > 0}>
          Try again
        </Button>
      )}
    </div>
  );
}
