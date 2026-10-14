import type { AnswerMap } from "../../api/types.ts";
import { formatValue } from "../../utils/format.ts";
import { MathFormula } from "./MathFormula.tsx";
import styles from "./result.module.css";

interface Props {
  answer: AnswerMap;
  /** variable -> "T = ..." in LaTeX. Used for symbolic answers only. */
  latex?: Record<string, string> | null;
}

export function AnswerList({ answer, latex }: Props) {
  return (
    <ul className={styles.answers} aria-label="Answer">
      {Object.entries(answer).map(([name, value]) => {
        // A string value means the problem was given in symbols, so the answer
        // is a formula. Show it as math when the engine sent LaTeX for it.
        const tex = typeof value === "string" ? latex?.[name] : undefined;
        return (
          <li key={name}>
            {tex ? (
              <MathFormula latex={tex} />
            ) : (
              <>
                <var className={styles.varName}>{name}</var> ={" "}
                <span className={styles.value}>{formatValue(value)}</span>
              </>
            )}
          </li>
        );
      })}
    </ul>
  );
}
