import { Fragment } from "react";
import { MathFormula } from "./MathFormula.tsx";

/**
 * Text with inline math between $...$, as the engine sends hints (see `hints` in
 * physics_mode_api.json). Text parts are shown as plain text; math parts go through
 * MathFormula, the same KaTeX renderer the solutions panel uses.
 *
 * If the $ signs don't pair up, the whole string is shown as plain text rather than
 * guessing which part was meant to be math.
 */
export function MathText({ text }: { text: string }) {
  const parts = text.split("$");
  if (parts.length % 2 === 0) return <>{text}</>;
  return (
    <>
      {parts.map((part, i) =>
        i % 2 === 0 ? (
          <Fragment key={i}>{part}</Fragment>
        ) : (
          <MathFormula key={i} latex={part} />
        ),
      )}
    </>
  );
}