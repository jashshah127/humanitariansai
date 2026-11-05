import { useEffect, useId, useRef, useState } from "react";
import { Button } from "../../design/components/Button.tsx";
import styles from "./result.module.css";

// Contract: an ordered ladder, each rung revealing more, answer last. One at a time.
// The parent resets this by changing its `key` when a new problem comes back.
export function HintLadder({ hints }: { hints: string[] }) {
  const headingId = useId();
  const [shown, setShown] = useState(1);
  const newestRef = useRef<HTMLLIElement>(null);
  const hasMore = shown < hints.length;
  const nextIsLast = shown === hints.length - 1;

  // After each reveal, move focus to the new hint: a screen reader reads it, and focus
  // isn't lost when the button disappears after the last one. Not on first load (shown 1).
  useEffect(() => {
    if (shown > 1) newestRef.current?.focus();
  }, [shown]);

  return (
    <section className={styles.section} aria-labelledby={headingId}>
      <h2 id={headingId} className={styles.heading}>
        Hints
      </h2>
      <ol className={styles.hints}>
        {hints.slice(0, shown).map((hint, i) => {
          const newest = i === shown - 1;
          return (
            <li key={i} ref={newest ? newestRef : undefined} tabIndex={newest ? -1 : undefined}>
              {hint}
            </li>
          );
        })}
      </ol>
      {hasMore && (
        <Button type="button" onClick={() => setShown(shown + 1)}>
          {nextIsLast ? "Show the answer" : "Show next hint"}
        </Button>
      )}
      {/* Not a live region: the focus move already reads the new hint. */}
      <p className={styles.counter}>
        {shown} of {hints.length} shown
      </p>
    </section>
  );
}