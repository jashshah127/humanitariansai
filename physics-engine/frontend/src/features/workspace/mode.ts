/** Longest problem we send. Protects the shared parse quota from pasted essays. */
export const MAX_CHARS = 1500;

/**
 * The three views of one problem. Not the same as api/types RenderMode: that is the
 * `render` value /solve accepts ("solve" | "tutor"). Grade uses its own endpoints, so
 * "grade" must never reach solve().
 */
export type WorkspaceMode = "solve" | "tutor" | "grade";

export const MODES: { value: WorkspaceMode; label: string; submit: string }[] = [
  { value: "solve", label: "Answer", submit: "Solve" },
  { value: "tutor", label: "Hints", submit: "Get hints" },
  { value: "grade", label: "Grade", submit: "Enter my answers" },
];

/** Reads ?mode= from the URL. Anything unknown falls back to "solve". */
export function parseMode(value: string | null): WorkspaceMode {
  return MODES.some((m) => m.value === value) ? (value as WorkspaceMode) : "solve";
}
