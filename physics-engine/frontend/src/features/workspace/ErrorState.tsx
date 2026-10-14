import type { ApiError } from "../../api/client.ts";
import styles from "./workspace.module.css";

export function ErrorState({ error }: { error: ApiError }) {
  const wait =
    error.kind === "rate" && error.retryAfter ? ` Try again in ${error.retryAfter} seconds.` : "";
  return (
    <p className={styles.error} role="alert">
      {error.message}
      {wait}
    </p>
  );
}
