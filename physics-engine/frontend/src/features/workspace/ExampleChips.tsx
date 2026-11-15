import { EXAMPLES } from "./examples.ts";
import styles from "./workspace.module.css";

const GROUPS = [
  { title: "Examples with a diagram:", items: EXAMPLES.filter((ex) => ex.diagram) },
  { title: "More examples:", items: EXAMPLES.filter((ex) => !ex.diagram) },
];

export function ExampleChips({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className={styles.exampleGroups}>
      {GROUPS.map((group) => (
        <p key={group.title} className={styles.examples}>
          <span>{group.title}</span>
          {group.items.map((ex) => (
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
      ))}
    </div>
  );
}
