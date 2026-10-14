import type { Candidate } from "../../api/types.ts";
import { formatValue } from "../../utils/format.ts";
import styles from "./result.module.css";

// Contract: show every candidate with its "applies when". Never pick one for the student.
export function CandidateList({ candidates }: { candidates: Candidate[] }) {
  return (
    <section className={styles.section} aria-labelledby="candidates-heading">
      <h2 id="candidates-heading" className={styles.heading}>
        More than one principle fits
      </h2>
      <p className={styles.lead}>
        Each one is worked out correctly. Pick the one whose conditions match your problem.
      </p>
      <ul className={styles.candidates}>
        {candidates.map((c, i) => (
          <li className={styles.candidate} key={`${c.principle}-${i}`}>
            <strong className={styles.principle}>{c.principle}</strong>
            <p className={styles.candidateMeta}>Use this when: {c.applies_when}</p>
            {c.answer && Object.keys(c.answer).length > 0 && (
              <p className={styles.candidateMeta}>
                Gives:{" "}
                {Object.entries(c.answer)
                  .map(([k, v]) => `${k} = ${formatValue(v)}`)
                  .join(", ")}
              </p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
