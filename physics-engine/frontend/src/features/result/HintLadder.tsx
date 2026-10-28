import { useState } from "react";
import { Button } from "../../design/components/Button.tsx";
import { MathText } from "./MathText.tsx";
import styles from "./result.module.css";

// Contract: an ordered ladder, each rung revealing more, answer last. One at a time.
// The parent resets this by changing its `key` when a new problem comes back.
export function HintLadder({ hints }: { hints: string[] }) {
  const [shown, setShown] = useState(1);
  const hasMore = shown < hints.length;
  const nextIsLast = shown === hints.length - 1;

  return (
    <section className={styles.section} aria-labelledby="hints-heading">
      <h2 id="hints-heading" className={styles.heading}>
        Hints
      </h2>
      <ol className={styles.hints}>
        {hints.slice(0, shown).map((hint, i) => (
                    <li key={i}>
            <MathText text={hint} />
          </li>
        ))}
      </ol>
      {hasMore && (
        <Button type="button" onClick={() => setShown(shown + 1)}>
          {nextIsLast ? "Show the answer" : "Show next hint"}
        </Button>
      )}
      <p className={styles.counter} aria-live="polite">
        {shown} of {hints.length} shown
      </p>
    </section>
  );
}
