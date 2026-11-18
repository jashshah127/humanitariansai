import { Link } from "react-router";
import type { LinkProps } from "react-router";
import { cx } from "../../utils/cx.ts";
import type { ButtonSize, ButtonVariant } from "./Button.tsx";
import styles from "./Button.module.css";

export interface ButtonLinkProps extends LinkProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

/**
 * A link that looks like a Button. Use it to go to another page, so "open in new tab",
 * middle-click and the browser's own link handling keep working. Use Button for actions.
 */
export function ButtonLink({
  variant = "primary",
  size = "md",
  className,
  ...rest
}: ButtonLinkProps) {
  return (
    <Link
      className={cx(styles.button, className)}
      data-variant={variant}
      data-size={size}
      {...rest}
    />
  );
}
