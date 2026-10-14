import { useId } from "react";
import { MAX_CHARS } from "./mode.ts";
import styles from "./workspace.module.css";

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function ProblemInput({ value, onChange, onSubmit }: Props) {
  const id = useId();
  const over = value.length > MAX_CHARS;

  return (
    <div>
      <label className={styles.label} htmlFor={id}>
        Your problem
      </label>
      <textarea
        id={id}
        className={styles.textarea}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            onSubmit();
          }
        }}
        placeholder="A car starts from rest and accelerates at 2.5 m/s^2 for 12 s. Find its final speed and distance."
        aria-invalid={over}
        aria-describedby={`${id}-meta`}
        spellCheck
      />
      <div id={`${id}-meta`} className={styles.inputMeta}>
        <span>Ctrl + Enter to submit</span>
        <span className={over ? styles.overLimit : undefined}>
          {over
            ? `${value.length - MAX_CHARS} characters over the limit`
            : `${value.length} / ${MAX_CHARS}`}
        </span>
      </div>
    </div>
  );
}
