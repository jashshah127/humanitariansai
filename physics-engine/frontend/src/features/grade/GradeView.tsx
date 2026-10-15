import type { GradeResponse, QuantitySpec } from "../../api/types.ts";
import { Button } from "../../design/components/Button.tsx";
import { Card } from "../../design/components/Card.tsx";
import { VerificationBadge } from "../../design/components/Badge.tsx";
import { formatValue } from "../../utils/format.ts";
import resultStyles from "../result/result.module.css";
import type { Assessment } from "./answer.ts";
import {
  canSeeReference,
  hasUnit,
  isWrong,
  normalizeAssessment,
  prettyUnit,
  REVEAL_AFTER_WRONG,
  sentenceCase,
} from "./answer.ts";
import styles from "./grade.module.css";

const VERDICT: Record<Assessment, string> = {
  correct: "Correct",
  wrong_value: "Not correct yet",
  wrong_method: "Not correct yet. This looks like a common mistake.",
  incomplete: "Some answers are missing",
  not_assessable: "This answer wasn't graded",
};

interface Props {
  data: GradeResponse;
  /** Asked-for quantities, in order, with labels and units (from /parse). */
  unknowns: QuantitySpec[];
  /** Wrong attempts on this problem so far, including this one. */
  wrongAttempts: number;
  /** The student pressed "Show the correct answer". */
  revealed: boolean;
  onReveal: () => void;
  busy?: boolean;
}

/**
 * Renders one /grade response. Badge first, as in ResultPanel.
 * Correct values follow ui_guidance.grade: hidden after the first wrong attempt,
 * shown after the second or when the student asks.
 */
export function GradeView({
  data,
  unknowns,
  wrongAttempts,
  revealed,
  onReveal,
  busy = false,
}: Props) {
  const assessment = normalizeAssessment(data.assessment);
  // Defensive: whatever the server says, "not graded" is never shown as verified.
  const state = assessment === "not_assessable" ? "unverified" : data.verification;
  const showReference = canSeeReference(wrongAttempts, revealed);
  const graded = assessment !== "not_assessable";

  return (
    <Card>
      <article className={resultStyles.result} data-state={state} aria-busy={busy}>
        <VerificationBadge state={state} label={data.badge} />

        <h2 className={styles.verdict} data-assessment={assessment}>
          {VERDICT[assessment]}
        </h2>

        {graded && unknowns.length > 0 && (
          <ul className={styles.rows} aria-label="Your answers, checked">
            {unknowns.map((u) => {
              const pq = data.per_quantity?.[u.name];
              const status = !pq ? "missing" : pq.correct ? "right" : "wrong";
              const reference = data.reference_answer?.[u.name] ?? pq?.reference;
              const unit = hasUnit(u.unit) ? ` ${prettyUnit(u.unit)}` : "";
              return (
                <li key={u.name} className={styles.row} data-status={status}>
                  <span className={styles.rowLabel}>
                    {sentenceCase(u.label)} (<var className={styles.varName}>{u.name}</var>)
                  </span>
                  <span className={styles.rowValue}>
                    {pq ? `You: ${formatValue(pq.submitted)}${unit}` : "No answer"}
                  </span>
                  <span className={styles.rowStatus}>
                    <span aria-hidden="true">
                      {status === "right" ? "\u2713" : status === "wrong" ? "\u2717" : "\u2013"}
                    </span>{" "}
                    {status === "right" ? "Right" : status === "wrong" ? "Wrong" : "Missing"}
                  </span>
                  {showReference && status !== "right" && reference !== undefined && (
                    <span className={styles.rowReference}>
                      Correct: {formatValue(reference)}
                      {unit}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        )}

        <p className={styles.feedback}>{data.feedback || "This answer couldn't be graded."}</p>

        {isWrong(assessment) && !showReference && (
          <div className={styles.next}>
            <p className={styles.nextText}>
              Change your answers above and check again.
              {wrongAttempts === REVEAL_AFTER_WRONG - 1 &&
                " The correct values appear after one more try."}
            </p>
            <Button type="button" variant="ghost" size="sm" onClick={onReveal}>
              Show the correct answer
            </Button>
          </div>
        )}
      </article>
    </Card>
  );
}
