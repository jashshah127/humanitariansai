import { cx } from "../../utils/cx.ts";
import styles from "./Skeleton.module.css";

export interface SkeletonProps {
  /** line: a row of text. pill: a badge. block: a large line, like an answer. */
  shape?: "line" | "pill" | "block";
  /** Any CSS width. A percentage keeps it responsive. */
  width?: string;
  className?: string;
}

/**
 * A grey placeholder in the shape of content that is still loading.
 * Always hidden from screen readers: pair it with a text status that says what is loading.
 */
export function Skeleton({ shape = "line", width = "100%", className }: SkeletonProps) {
  return (
    <span
      className={cx(styles.skeleton, className)}
      data-shape={shape}
      style={{ width }}
      aria-hidden="true"
    />
  );
}
