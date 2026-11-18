import type { LogEntry } from "../../api/problemLog.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import type { VerificationState } from "../../design/components/verification.ts";

export const ALL = "all";
/** Topic filter value for rows the tagger hasn't tagged yet. */
export const UNTAGGED = "untagged";

export interface LogFilters {
  search: string;
  review: "all" | "needs_review" | "reviewed";
  /** ALL, UNTAGGED, or a topic name. */
  topic: string;
  verification: VerificationState | "all";
}

export const NO_LOG_FILTERS: LogFilters = { search: "", review: "all", topic: ALL, verification: "all" };

export function filterLog(rows: LogEntry[], f: LogFilters): LogEntry[] {
  const q = f.search.trim().toLowerCase();
  return rows.filter(
    (r) =>
      (f.review === "all" || r.needs_review === (f.review === "needs_review")) &&
      (f.topic === ALL || (f.topic === UNTAGGED ? !r.topic : r.topic === f.topic)) &&
      (f.verification === "all" || normalizeVerification(r.verification) === f.verification) &&
      (!q || r.problem_text.toLowerCase().includes(q)),
  );
}