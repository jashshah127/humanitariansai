import { MODES } from "./mode.ts";
import type { WorkspaceMode } from "./mode.ts";
import styles from "./workspace.module.css";

const WHAT_YOU_GET: Record<WorkspaceMode, string> = {
  solve: "You’ll get the answer and how it was worked out.",
  tutor: "Hints come one at a time. The answer comes last.",
  grade:
    "You’ll get one box for each quantity the problem asks for, and the engine checks what you type.",
};

/** Fills the space under the form until the first result, so it isn't blank. */
export function EmptyWorkspace({ mode }: { mode: WorkspaceMode }) {
  const submit = MODES.find((m) => m.value === mode)?.submit ?? "Solve";
  return (
    <div className={styles.empty}>
      <p className={styles.emptyText}>
        Type a problem above and press “{submit}”. {WHAT_YOU_GET[mode]}
      </p>
      <p className={styles.emptyText}>
        Every result starts with a label that says how far to trust it:
      </p>
      <ul className={styles.emptyList}>
        <li>
          <strong>Verified</strong>: a symbolic solver checked it.
        </li>
        <li>
          <strong>Needs review</strong>: more than one principle fits, so you choose.
        </li>
        <li>
          <strong>Unverified</strong>: nothing checked it. Check it yourself before you rely on it.
        </li>
      </ul>
    </div>
  );
}
