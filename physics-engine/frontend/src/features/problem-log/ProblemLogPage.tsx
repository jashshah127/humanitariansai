import { useEffect, useState } from "react";
import { Link } from "react-router";
import { DIFFICULTY_LABELS, GRADE_LABELS, problemLogStore } from "../../api/problemLog.ts";
import type { LogEntry, ProblemLogStore } from "../../api/problemLog.ts";
import { VerificationBadge } from "../../design/components/Badge.tsx";
import { Button } from "../../design/components/Button.tsx";
import { Input, Select } from "../../design/components/Input.tsx";
import { DEFAULT_LABELS, VERIFICATION_STATES } from "../../design/components/verification.ts";
import type { VerificationState } from "../../design/components/verification.ts";
import { AdminOnly } from "./AdminOnly.tsx";
import { formatHour, preview } from "./display.ts";
import { ALL, filterLog, NO_LOG_FILTERS, UNTAGGED } from "./filterLog.ts";
import type { LogFilters } from "./filterLog.ts";
import styles from "./problemLog.module.css";

/** /app/history: every logged problem, for admins to review and fix tags. */
export default function ProblemLogPage({ store = problemLogStore }: { store?: ProblemLogStore }) {
  return (
    <AdminOnly store={store}>
      <LogList store={store} />
    </AdminOnly>
  );
}

type Load = { status: "loading" } | { status: "error" } | { status: "ready"; rows: LogEntry[] };

function LogList({ store }: { store: ProblemLogStore }) {
  const [load, setLoad] = useState<Load>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [filters, setFilters] = useState<LogFilters>(NO_LOG_FILTERS);
  const set = (patch: Partial<LogFilters>) => setFilters((f) => ({ ...f, ...patch }));

  useEffect(() => {
    let live = true;
    store.list().then(
      (rows) => {
        if (live) setLoad({ status: "ready", rows });
      },
      (e: unknown) => {
        console.error("[problem log] list failed", e);
        if (live) setLoad({ status: "error" });
      },
    );
    return () => {
      live = false;
    };
  }, [store, attempt]);

  const rows = load.status === "ready" ? load.rows : [];
  const shown = filterLog(rows, filters);
  const flagged = rows.filter((r) => r.needs_review).length;
  const topics = [...new Set(rows.map((r) => r.topic).filter((t): t is string => !!t))].sort();

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <Link to="/app" className={styles.back}>
          ← Back to the workspace
        </Link>
        <h1 className={styles.title}>Problem logs</h1>
        <p className={styles.lead}>
          Every problem asked, with its tags. Personal details are removed and no row says who asked
          it.
        </p>
      </header>

      {load.status === "loading" && <p className={styles.status}>Loading…</p>}

      {load.status === "error" && (
        <div role="alert" className={styles.notice}>
          <p>The problem history couldn’t be loaded. Check your connection and try again.</p>
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

      {load.status === "ready" && rows.length === 0 && (
        <p className={styles.status}>
          Nothing logged yet. Problems appear here once the server’s problem log is turned on and
          someone solves one.
        </p>
      )}

      {load.status === "ready" && rows.length > 0 && (
        <>
          {flagged > 0 && (
            <p className={styles.notice}>
              {flagged === 1 ? "1 problem needs" : `${flagged} problems need`} review.
              <Button variant="secondary" size="sm" onClick={() => set({ review: "needs_review" })}>
                Show them
              </Button>
            </p>
          )}

          <div className={styles.filters}>
            <Input
              label="Search"
              type="search"
              value={filters.search}
              placeholder="e.g. pulley"
              onChange={(e) => set({ search: e.target.value })}
            />
            <Select
              label="Review"
              value={filters.review}
              onChange={(e) => set({ review: e.target.value as LogFilters["review"] })}
            >
              <option value="all">All</option>
              <option value="needs_review">Needs review</option>
              <option value="reviewed">Doesn’t need review</option>
            </Select>
            <Select
              label="Topic"
              value={filters.topic}
              onChange={(e) => set({ topic: e.target.value })}
            >
              <option value={ALL}>All</option>
              {topics.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
              <option value={UNTAGGED}>Not tagged</option>
            </Select>
            <Select
              label="Verification"
              value={filters.verification}
              onChange={(e) => set({ verification: e.target.value as VerificationState | "all" })}
            >
              <option value="all">All</option>
              {VERIFICATION_STATES.map((s) => (
                <option key={s} value={s}>
                  {DEFAULT_LABELS[s]}
                </option>
              ))}
            </Select>
          </div>

          <p className={styles.status} aria-live="polite">
            Showing {shown.length} of {rows.length}
          </p>

          {shown.length === 0 ? (
            <p className={styles.status}>
              No problems match.{" "}
              <Button variant="ghost" size="sm" onClick={() => setFilters(NO_LOG_FILTERS)}>
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
                    {r.needs_review && <span className={styles.flag}>Needs review</span>}
                    <VerificationBadge state={r.verification} />
                    <span>{r.topic ? `${r.topic} · ${r.subtopic ?? ""}` : "Not tagged"}</span>
                    {r.grade_level && <span>{GRADE_LABELS[r.grade_level] ?? r.grade_level}</span>}
                    {r.difficulty && <span>{DIFFICULTY_LABELS[r.difficulty] ?? r.difficulty}</span>}
                    <time dateTime={r.created_at}>{formatHour(r.created_at)}</time>
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
