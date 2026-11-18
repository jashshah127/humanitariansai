import { useEffect, useId, useState } from "react";
import { Link } from "react-router";
import { historyStore } from "../../api/history.ts";
import type { HistoryEntry, HistoryStore } from "../../api/history.ts";
import { VerificationBadge } from "../../design/components/Badge.tsx";
import { Button } from "../../design/components/Button.tsx";
import { Input } from "../../design/components/Input.tsx";
import { DEFAULT_LABELS, VERIFICATION_STATES } from "../../design/components/verification.ts";
import { formatWhen, MODE_LABELS, preview } from "./display.ts";
import { filterHistory } from "./filterHistory.ts";
import type { StateFilter } from "./filterHistory.ts";
import styles from "./history.module.css";

type Load = { status: "loading" } | { status: "error" } | { status: "ready"; rows: HistoryEntry[] };

/** /app/history: the signed-in user's past problems, with search and a verification filter. */
export default function HistoryPage({ store = historyStore }: { store?: HistoryStore }) {
  const [load, setLoad] = useState<Load>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [search, setSearch] = useState("");
  const [state, setState] = useState<StateFilter>("all");
  const selectId = useId();

  useEffect(() => {
    let live = true;
    store.list().then(
      (rows) => {
        if (live) setLoad({ status: "ready", rows });
      },
      (e: unknown) => {
        console.error("[history] list failed", e);
        if (live) setLoad({ status: "error" });
      },
    );
    return () => {
      live = false;
    };
  }, [store, attempt]);

  function retry() {
    setLoad({ status: "loading" });
    setAttempt((n) => n + 1);
  }

  const rows = load.status === "ready" ? load.rows : [];
  const shown = filterHistory(rows, search, state);

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <Link to="/app" className={styles.back}>
          ← Back to the workspace
        </Link>
        <h1 className={styles.title}>Your problems</h1>
        <p className={styles.lead}>
          Problems you’ve worked on, newest first. Only you can see them.
        </p>
      </header>

      {load.status === "loading" && <p className={styles.status}>Loading your history…</p>}

      {load.status === "error" && (
        <div role="alert" className={styles.notice}>
          <p>Your history couldn’t be loaded. Check your connection and try again.</p>
          <Button variant="secondary" size="sm" onClick={retry}>
            Try again
          </Button>
        </div>
      )}

      {load.status === "ready" && rows.length === 0 && (
        <p className={styles.status}>
          No problems yet. Problems you solve will show up here.{" "}
          <Link to="/app">Solve one now</Link>.
        </p>
      )}

      {load.status === "ready" && rows.length > 0 && (
        <>
          <div className={styles.filters}>
            <Input
              label="Search"
              type="search"
              value={search}
              placeholder="e.g. pulley"
              onChange={(e) => setSearch(e.target.value)}
            />
            <div>
              <label htmlFor={selectId} className={styles.label}>
                Verification
              </label>
              <select
                id={selectId}
                className={styles.select}
                value={state}
                onChange={(e) => setState(e.target.value as StateFilter)}
              >
                <option value="all">All</option>
                {VERIFICATION_STATES.map((s) => (
                  <option key={s} value={s}>
                    {DEFAULT_LABELS[s]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <p className={styles.status} aria-live="polite">
            Showing {shown.length} of {rows.length}
          </p>

          {shown.length === 0 ? (
            <p className={styles.status}>
              No problems match.{" "}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSearch("");
                  setState("all");
                }}
              >
                Clear filters
              </Button>
            </p>
          ) : (
            <ul className={styles.list}>
              {shown.map((r) => (
                <li key={r.id} className={styles.item}>
                  <Link to={`/app/history/${r.id}`} className={styles.itemLink}>
                    {preview(r.problem_text)}
                  </Link>
                  <div className={styles.meta}>
                    <VerificationBadge state={r.verification} />
                    <span>{MODE_LABELS[r.mode] ?? r.mode}</span>
                    <time dateTime={r.created_at}>{formatWhen(r.created_at)}</time>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </main>
  );
}
