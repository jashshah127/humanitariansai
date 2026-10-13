import { useId } from "react";
import type { HTMLAttributes, ReactNode } from "react";
import { cx } from "../../utils/cx.ts";
import styles from "./Card.module.css";

export interface CardProps extends Omit<HTMLAttributes<HTMLElement>, "title"> {
  title?: ReactNode;
  /** Pick the level that fits the page's heading outline. */
  headingLevel?: 2 | 3 | 4;
  padding?: "sm" | "md" | "lg";
  as?: "section" | "article" | "div";
  children: ReactNode;
}

export function Card({
  title,
  headingLevel = 3,
  padding = "md",
  as: Tag = "section",
  className,
  children,
  ...rest
}: CardProps) {
  const titleId = useId();
  const Heading = `h${headingLevel}` as "h2" | "h3" | "h4";
  return (
    <Tag
      className={cx(styles.card, className)}
      data-padding={padding}
      aria-labelledby={title ? titleId : undefined}
      {...rest}
    >
      {title && (
        <Heading id={titleId} className={styles.title}>
          {title}
        </Heading>
      )}
      {children}
    </Tag>
  );
}
