// Pure helpers for grade mode. Kept out of the components so they can be tested
// directly and so component files only export components (react-refresh rule).

export type Assessment =
  "correct" | "wrong_value" | "wrong_method" | "incomplete" | "not_assessable";

const ASSESSMENTS: readonly string[] = [
  "correct",
  "wrong_value",
  "wrong_method",
  "incomplete",
  "not_assessable",
];

/** Anything unknown or missing is treated as "not graded", never as a grade. */
export function normalizeAssessment(value: unknown): Assessment {
  return typeof value === "string" && ASSESSMENTS.includes(value)
    ? (value as Assessment)
    : "not_assessable";
}

export function isWrong(a: Assessment): boolean {
  return a === "wrong_value" || a === "wrong_method";
}

/**
 * ui_guidance.grade in the contract: after the FIRST wrong attempt the correct values
 * stay hidden; after the second, or when the student asks, they are shown.
 * This only prevents accidental spoilers: the values are in the response.
 */
export const REVEAL_AFTER_WRONG = 2;

export function canSeeReference(wrongAttempts: number, askedToSee: boolean): boolean {
  return askedToSee || wrongAttempts >= REVEAL_AFTER_WRONG;
}

export type ParsedAnswer = { ok: true; value: number } | { ok: false; error: string };

const NUMBER = /^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i;
const NUMBER_THEN_TEXT = /^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?\s*[^\d\s.,]/i;

/**
 * Reads what a student typed into one answer box.
 * Accepts 1.96, -1.96, .5, 4.7e1. Rejects commas (is "1,5" one and a half, or 15?)
 * and typed units, with a message that says how to fix it.
 */
export function parseAnswer(raw: string, unit = ""): ParsedAnswer {
  // A typographic minus (copied from a PDF or a calculator app) is still a minus.
  const text = raw.trim().replace(/\u2212/g, "-");
  if (text === "") return { ok: false, error: "Enter a number." };
  if (text.includes(",")) return { ok: false, error: "Use a dot for decimals, and no commas." };
  if (!NUMBER.test(text)) {
    // Checked only after NUMBER fails, or the "e" in 4.7e1 would count as a typed unit.
    if (NUMBER_THEN_TEXT.test(text)) {
      return {
        ok: false,
        error: hasUnit(unit)
          ? `Enter only the number. The unit is already set: ${unit}.`
          : "Enter only the number.",
      };
    }
    return { ok: false, error: "Enter a number, like 9.8 or -1.5e3." };
  }
  const value = Number(text);
  if (!Number.isFinite(value)) return { ok: false, error: "That number is too large." };
  return { ok: true, value };
}

/** "" and "dimensionless" mean there is no unit to show. */
export function hasUnit(unit: string): boolean {
  return unit !== "" && unit !== "dimensionless";
}

/** "linear acceleration" -> "Linear acceleration". */
export function sentenceCase(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** "m/s^2" -> "m/s²". Display only; the unit string itself is never changed. */
export function prettyUnit(unit: string): string {
  return unit.replace(/\^2/g, "\u00b2").replace(/\^3/g, "\u00b3");
}
