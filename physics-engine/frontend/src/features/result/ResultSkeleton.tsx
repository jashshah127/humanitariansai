import { Card } from "../../design/components/Card.tsx";
import { Skeleton } from "../../design/components/Skeleton.tsx";
import styles from "./result.module.css";

/**
 * The outline of a result card -- badge, answer, explanation -- shown while the
 * first answer loads. Hidden from screen readers: the "Working on it…" status
 * above it already says what is happening.
 */
export function ResultSkeleton() {
  return (
    <Card as="div" aria-hidden="true" data-testid="result-skeleton">
      <div className={styles.skeleton}>
        <Skeleton shape="pill" width="11rem" />
        <Skeleton shape="block" width="55%" />
        <Skeleton width="100%" />
        <Skeleton width="92%" />
        <Skeleton width="68%" />
      </div>
    </Card>
  );
}
