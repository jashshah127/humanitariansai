import type { RenderMode } from "../../api/types.ts";

/** Longest problem we send. Protects the shared parse quota from pasted essays. */
export const MAX_CHARS = 1500;

// Grade joins this list once the B4/B5 decisions are made.
export const MODES: { value: RenderMode; label: string; submit: string }[] = [
  { value: "solve", label: "Answer", submit: "Solve" },
  { value: "tutor", label: "Hints", submit: "Get hints" },
];

/** Reads ?mode= from the URL. Anything unknown falls back to "solve". */
export function parseMode(value: string | null): RenderMode {
  return MODES.some((m) => m.value === value) ? (value as RenderMode) : "solve";
}
