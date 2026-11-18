import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { historyStore } from "../../api/history.ts";
import type { HistoryEntry, HistoryStore } from "../../api/history.ts";
import { VerificationBadge } from "../../design/components/Badge.tsx";
import { Button } from "../../design/components/Button.tsx";
import { formatValue } from "../../utils/format.ts";
import { formatWhen, MODE_LABELS } from "./display.ts";
import styles from "./history.module.css";

type Load =
  | { status: "loading" }
  | { status: "error" }
  | { status: "missing" }
  | { status: "ready"; row: HistoryEntry };

/** What WorkspacePage reads from the router state to fill in the problem box. */
export interface ReopenState {
  problem: string;
}

/** /app/history/:id: one past problem, with "open in the workspace" and delete. */
export default function HistoryDetailPage({ store = historyStore }: { store?: HistoryStore }) {
  const { id } = useParams();
  const num = Number(id);
  const valid = Number.isInteger(num) && num > 0;
  const navigate = useNavigate();

  const [load, setLoad] = useState<Load>(valid ? { status: "loading" } : { status: "missing" });
  const [attempt, setAttempt] = useState(0);
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteFailed, setDeleteFailed] = useState(false);

  useEffect(() => {
    if (!valid) return;
    let live = true;
    store.get(num).then(
      (row) => {
        if (live) setLoad(row ? { status: "ready", row } : { status: "missing" });
      },
      (e: unknown) => {
        console.error("[history] get failed", e);
        if (live) setLoad({ status: "error" });
      },
    );
    return () => {
      live = false;
    };
  }, [store, num, valid, attempt]);

  async function remove(row: HistoryEntry) {
    setDeleting(true);
    setDeleteFailed(false);
    try {
      await store.remove(row.id);
      navigate("/app/history", { replace: true });
    } catch (e) {
      console.error("[history] delete failed", e);
      setDeleteFailed(true);
      setDeleting(false);
    }
  }

  function reopen(row: HistoryEntry) {
    const state: ReopenState = { problem: row.problem_text };
    navigate(`/app?mode=${encodeURIComponent(row.mode)}`, { state });
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <Link to="/app/history" className={styles.back}>
          ← All your problems
        </Link>
      </header>

      {load.status === "loading" && <p className={styles.status}>Loading…</p>}

      {load.status === "error" && (
        <div role="alert" className={styles.notice}>
          <p>This problem couldn’t be loaded. Check your connection and try again.</p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              setLoad({ status: "loading" });
              setAttempt((n) => n + 1);
            }}
          >
            Try again
          </Button>
        </div>
      )}

      {load.status === "missing" && (
        <>
          <h1 className={styles.title}>Problem not found</h1>
          <p className={styles.status}>
            It may have been deleted. <Link to="/app/history">See all your problems</Link>.
          </p>
        </>
      )}

      {load.status === "ready" && (
        <article>
          <h1 className={styles.title}>Past problem</h1>
          <div className={styles.meta}>
            <VerificationBadge state={load.row.verification} />
            <span>{MODE_LABELS[load.row.mode] ?? load.row.mode}</span>
            <time dateTime={load.row.created_at}>{formatWhen(load.row.created_at)}</time>
          </div>

          <p className={styles.problem}>{load.row.problem_text}</p>

          {load.row.answer && Object.keys(load.row.answer).length > 0 && (
            <dl className={styles.answers}>
              {Object.entries(load.row.answer).map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{formatValue(v)}</dd>
                </div>
              ))}
            </dl>
          )}

          <div className={styles.actions}>
            <Button onClick={() => reopen(load.row)}>Open in the workspace</Button>
            {!confirming ? (
              <Button variant="ghost" onClick={() => setConfirming(true)}>
                Delete
              </Button>
            ) : (
              <span className={styles.confirm}>
                Delete this problem for good?
                <Button
                  variant="secondary"
                  size="sm"
                  loading={deleting}
                  onClick={() => void remove(load.row)}
                >
                  Yes, delete
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={deleting}
                  onClick={() => setConfirming(false)}
                >
                  Cancel
                </Button>
              </span>
            )}
          </div>
          {deleteFailed && (
            <p role="alert" className={styles.status}>
              It couldn’t be deleted. Try again.
            </p>
          )}
          <p className={styles.status}>
            Opening it fills in the workspace. Solving it again uses part of the shared daily quota.
          </p>
        </article>
      )}
    </main>
  );
}
