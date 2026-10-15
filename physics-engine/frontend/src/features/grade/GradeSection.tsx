import { useState } from "react";
import type { GradeResponse, ParseResponse } from "../../api/types.ts";
import { Button } from "../../design/components/Button.tsx";
import { Card } from "../../design/components/Card.tsx";
import { VerificationBadge } from "../../design/components/Badge.tsx";
import resultStyles from "../result/result.module.css";
import { GradeView } from "./GradeView.tsx";
import { StudentAnswerForm } from "./StudentAnswerForm.tsx";
import styles from "./grade.module.css";

interface Props {
  setup: ParseResponse;
  graded: GradeResponse | null;
  /** Changes with every new /grade response, to reset per-response state. */
  gradedId: number;
  wrongAttempts: number;
  onCheck: (answers: Record<string, number>) => void;
  onReread: () => void;
  busy?: boolean;
}

/**
 * Grade mode for one problem: the answer boxes, then the result under them.
 * The parent gives this a new `key` for each new problem, which clears the typed
 * values and the "show the answer" choice.
 */
export function GradeSection({
  setup,
  graded,
  gradedId,
  wrongAttempts,
  onCheck,
  onReread,
  busy = false,
}: Props) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [revealed, setRevealed] = useState(false);

  if (!setup.gradable || !setup.parsed || setup.unknowns.length === 0) {
    return (
      <Card>
        <article className={resultStyles.result} data-state="unverified" aria-busy={busy}>
          <VerificationBadge state="unverified" label="Unverified - can't be graded" />
          <p className={styles.feedback}>
            {setup.reason || "This problem can't be graded automatically."}
          </p>
          <p className={resultStyles.explanation}>
            Answer and Hints may still help with it. If the engine misread the problem, try reading
            it again.
          </p>
          <div className={styles.next}>
            <Button type="button" variant="ghost" size="sm" onClick={onReread} disabled={busy}>
              Read the problem again
            </Button>
          </div>
        </article>
      </Card>
    );
  }

  return (
    <div className={styles.stack}>
      <Card>
        <StudentAnswerForm
          unknowns={setup.unknowns}
          given={setup.given}
          values={values}
          onChange={(name, value) => setValues((prev) => ({ ...prev, [name]: value }))}
          onCheck={onCheck}
          onReread={onReread}
          busy={busy}
        />
      </Card>
      {graded && (
        <GradeView
          key={gradedId}
          data={graded}
          unknowns={setup.unknowns}
          wrongAttempts={wrongAttempts}
          revealed={revealed}
          onReveal={() => setRevealed(true)}
          busy={busy}
        />
      )}
    </div>
  );
}
