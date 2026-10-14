import type { SolveResponse } from "../../api/types.ts";
import { MathFormula } from "./MathFormula.tsx";
import styles from "./result.module.css";

type Props = Pick<
  SolveResponse,
  "formula_used" | "assumptions" | "sources" | "formula_latex" | "general_answer_latex"
>;

/** Why a student should believe the answer: the principle, its equations, its conditions, and what was read. */
export function WhyPanel({
  formula_used,
  assumptions,
  sources,
  formula_latex,
  general_answer_latex,
}: Props) {
  // Drop variables with no source phrase, so we never show `v from "null"`.
  const sourceList = Object.entries(sources ?? {}).filter(
    (entry): entry is [string, string] => !!entry[1],
  );
  const assumptionList = assumptions ?? [];
  const equations = formula_latex ?? [];
  const general = Object.values(general_answer_latex ?? {});

  if (
    !formula_used &&
    assumptionList.length === 0 &&
    sourceList.length === 0 &&
    equations.length === 0
  )
    return null;

  return (
    <section className={styles.section} aria-labelledby="why-heading">
      <h2 id="why-heading" className={styles.heading}>
        How this was worked out
      </h2>
      <dl className={styles.facts}>
        {formula_used && (
          <>
            <dt>Principle used</dt>
            <dd>{formula_used}</dd>
          </>
        )}
        {equations.length > 0 && (
          <>
            <dt>Equations</dt>
            <dd>
              {equations.map((tex, i) => (
                <MathFormula key={i} latex={tex} display />
              ))}
            </dd>
          </>
        )}
        {general.length > 0 && (
          <>
            <dt>Rearranged for what you asked</dt>
            <dd>
              {general.map((tex, i) => (
                <MathFormula key={i} latex={tex} display />
              ))}
            </dd>
          </>
        )}
        {assumptionList.length > 0 && (
          <>
            <dt>This assumes</dt>
            <dd>
              <ul className={styles.plainList}>
                {assumptionList.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </dd>
          </>
        )}
        {sourceList.length > 0 && (
          <>
            <dt>Read from your problem</dt>
            <dd>
              <ul className={styles.plainList}>
                {sourceList.map(([name, phrase]) => (
                  <li key={name}>
                    <var className={styles.varName}>{name}</var> from “{phrase}”
                  </li>
                ))}
              </ul>
            </dd>
          </>
        )}
      </dl>
    </section>
  );
}
