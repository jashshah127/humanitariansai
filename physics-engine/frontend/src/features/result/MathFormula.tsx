import { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import styles from "./result.module.css";

interface Props {
  latex: string;
  /** Block (centered, larger) instead of inline. */
  display?: boolean;
}

/**
 * Renders LaTeX from the engine with KaTeX.
 * - trust: false blocks \href, \url and similar commands, so engine output
 *   can't inject links or HTML. KaTeX escapes everything else.
 * - throwOnError: false shows bad LaTeX in red instead of crashing the page.
 * - The default output includes MathML, so screen readers can read the math.
 * If KaTeX still fails for any reason, the raw LaTeX is shown as code.
 */
export function MathFormula({ latex, display = false }: Props) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(latex, {
        displayMode: display,
        throwOnError: false,
        trust: false,
        strict: "ignore",
      });
    } catch {
      return null;
    }
  }, [latex, display]);

  if (html === null) return <code>{latex}</code>;
  return (
    <span
      className={display ? styles.mathBlock : styles.mathInline}
      // Safe: KaTeX output with trust: false, built from engine data only.
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
