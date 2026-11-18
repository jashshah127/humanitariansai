import type { HistoryMode } from "../../api/history.ts";

/** Same words the workspace's mode toggle uses (features/workspace/mode.ts). */
export const MODE_LABELS: Record<HistoryMode, string> = {
  solve: "Answer",
  tutor: "Hints",
  grade: "Grade",
};

/** "14 Nov 2026, 15:20" in the reader's own locale; "" for a bad date. */
export function formatWhen(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(d);
}

/** One line of the problem for the list: whitespace collapsed, long text cut. */
export function preview(text: string, max = 140): string {
  const t = text.replace(/\s+/g, " ").trim();
  return t.length > max ? `${t.slice(0, max - 1)}…` : t;
}