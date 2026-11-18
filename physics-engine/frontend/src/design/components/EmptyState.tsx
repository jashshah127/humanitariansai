import type { ReactNode } from "react";
import styles from "./EmptyState.module.css";

export interface EmptyStateProps {
  title: ReactNode;
  /** One or two short sentences: what happened, and what to do next. */
  children?: ReactNode;
  /** The next step: a Button or a Link. */
  action?: ReactNode;
  /** 1 when the empty state is the whole page; 2 or 3 inside a page. */
  headingLevel?: 1 | 2 | 3;
}

/**
 * A screen with nothing to show: a missing page, a crash, no history yet, no matches.
 * Always says what to do next; never just "Nothing here".
 */
export function EmptyState({ title, children, action, headingLevel = 2 }: EmptyStateProps) {
  const Heading = `h${headingLevel}` as "h1" | "h2" | "h3";
  return (
    <div className={styles.empty}>
      <Heading className={styles.title}>{title}</Heading>
      {children && <div className={styles.body}>{children}</div>}
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
}
