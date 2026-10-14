import { EXAMPLES } from "./examples.ts";
import styles from "./workspace.module.css";

export function ExampleChips({ onPick }: { onPick: (text: string) => void }) {
  return (
    <p className={styles.examples}>
      <span>Try an example:</span>
      {EXAMPLES.map((ex) => (
        <button
          key={ex.label}
          type="button"
          className={styles.exampleButton}
          onClick={() => onPick(ex.text)}
        >
          {ex.label}
        </button>
      ))}
    </p>
  );
}
