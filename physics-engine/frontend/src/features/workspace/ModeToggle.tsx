import type { RenderMode } from "../../api/types.ts";
import { MODES } from "./mode.ts";
import styles from "./workspace.module.css";

interface Props {
  value: RenderMode;
  onChange: (mode: RenderMode) => void;
  disabled?: boolean;
}

// Sits next to the input, per the contract ("a mode selector attached to the input").
export function ModeToggle({ value, onChange, disabled = false }: Props) {
  return (
    <fieldset className={styles.toggle} disabled={disabled}>
      <legend className={styles.srOnly}>Show me</legend>
      {MODES.map((m) => (
        <label key={m.value} className={styles.option}>
          <input
            className={styles.srOnly}
            type="radio"
            name="mode"
            value={m.value}
            checked={value === m.value}
            onChange={() => onChange(m.value)}
          />
          {m.label}
        </label>
      ))}
    </fieldset>
  );
}
