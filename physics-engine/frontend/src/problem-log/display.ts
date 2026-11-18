import type { TagSource } from "../../api/problemLog.ts";

export const TAG_SOURCE_LABELS: Record<TagSource, string> = {
  engine_card: "Formula card",
  llm: "AI model",
  admin: "Admin",
};

/** created_at is a whole hour, so show the hour, not minutes: "Nov 15, 2026, 3 PM". */
export function formatHour(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
  }).format(d);
}

/** For admin edit stamps, which are exact. */
export function formatExact(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(d);
}

/** One line of the problem for the list: whitespace collapsed, long text cut. */
export function preview(text: string, max = 140): string {
  const t = text.replace(/\s+/g, " ").trim();
  return t.length > max ? `${t.slice(0, max - 1)}…` : t;
}