import { forwardRef, useId } from "react";
import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";
import { cx } from "../../utils/cx.ts";
import styles from "./Input.module.css";

interface FieldProps {
  /** Always required: every input needs a visible label. */
  label: string;
  /** Short help text under the label. */
  hint?: ReactNode;
  /** Error message. When set, the field is marked invalid. */
  error?: ReactNode;
}

function useFieldIds(id: string | undefined, hint: ReactNode, error: ReactNode) {
  const autoId = useId();
  const controlId = id ?? autoId;
  const hintId = hint ? `${controlId}-hint` : undefined;
  const errorId = error ? `${controlId}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  return { controlId, hintId, errorId, describedBy };
}

export type InputProps = InputHTMLAttributes<HTMLInputElement> & FieldProps;

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, error, id, className, ...rest },
  ref,
) {
  const ids = useFieldIds(id, hint, error);
  return (
    <div className={styles.field}>
      <label htmlFor={ids.controlId} className={styles.label}>
        {label}
      </label>
      {hint && (
        <p id={ids.hintId} className={styles.hint}>
          {hint}
        </p>
      )}
      <input
        ref={ref}
        id={ids.controlId}
        className={cx(styles.control, className)}
        aria-invalid={error ? true : undefined}
        aria-describedby={ids.describedBy}
        {...rest}
      />
      {error && (
        <p id={ids.errorId} className={styles.error}>
          {error}
        </p>
      )}
    </div>
  );
});

export type TextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & FieldProps;

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(function TextArea(
  { label, hint, error, id, className, rows = 4, ...rest },
  ref,
) {
  const ids = useFieldIds(id, hint, error);
  // Character count, only when the length is known (controlled value + maxLength).
  const count =
    typeof rest.value === "string" && rest.maxLength
      ? `${rest.value.length} / ${rest.maxLength}`
      : null;

  return (
    <div className={styles.field}>
      <label htmlFor={ids.controlId} className={styles.label}>
        {label}
      </label>
      {hint && (
        <p id={ids.hintId} className={styles.hint}>
          {hint}
        </p>
      )}
      <textarea
        ref={ref}
        id={ids.controlId}
        rows={rows}
        className={cx(styles.control, styles.textarea, className)}
        aria-invalid={error ? true : undefined}
        aria-describedby={ids.describedBy}
        {...rest}
      />
      {(error || count) && (
        <div className={styles.footer}>
          {error ? (
            <p id={ids.errorId} className={styles.error}>
              {error}
            </p>
          ) : (
            <span />
          )}
          {count && <span className={styles.count}>{count}</span>}
        </div>
      )}
    </div>
  );
});
