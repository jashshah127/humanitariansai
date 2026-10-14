import type { AnswerValue } from "../api/types.ts";

/** 5 significant figures for numbers; symbolic answers are shown as sent. */
export function formatValue(v: AnswerValue): string {
  return typeof v === "number" ? Number(v.toPrecision(5)).toString() : String(v);
}
