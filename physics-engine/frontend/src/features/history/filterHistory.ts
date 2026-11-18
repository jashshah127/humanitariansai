import type { HistoryEntry } from "../../api/history.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import type { VerificationState } from "../../design/components/verification.ts";

export type StateFilter = VerificationState | "all";

/** Text search (case-insensitive, in the problem text) plus a verification filter. */
export function filterHistory(
  rows: HistoryEntry[],
  search: string,
  state: StateFilter,
): HistoryEntry[] {
  const q = search.trim().toLowerCase();
  return rows.filter(
    (r) =>
      (state === "all" || normalizeVerification(r.verification) === state) &&
      (!q || r.problem_text.toLowerCase().includes(q)),
  );
}
