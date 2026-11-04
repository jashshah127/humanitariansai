import { formatValue } from "../../utils/format.ts";
import type { CircularData } from "./circular.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 340;
const CX = 300;
const CY = 180;
const R = 120; // fixed drawing size; the real radius is shown as a number

/**
 * Circular path of a charged particle in a magnetic field, drawn from the
 * verified answer. The problem does not say which way B points, so the drawing
 * shows no direction of travel and no into/out-of-page field symbols. Showing
 * one would be a guess presented as a fact.
 */
export function CircularPathDiagram({ data }: { data: CircularData }) {
  const r = formatValue(data.r);
  const T = formatValue(data.T);
  const B = formatValue(data.B);
  const v = formatValue(data.v);
  const summary =
    `Charged particle at ${v} m/s in a ${B} T magnetic field moves in a circle of radius ` +
    `r = ${r} m and goes once around every T = ${T} s. ` +
    `The direction of travel is not shown because the problem does not give the field direction.`;

  return (
    <figure className={styles.figure}>
      <svg viewBox={`0 0 ${W} ${H}`} className={styles.svg} role="img" aria-label={summary}>
        <text className={styles.label} x={24} y={34}>
          Uniform field B = {B} T,
        </text>
        <text className={styles.label} x={24} y={54}>
          at right angles to the page
        </text>

        <circle className={styles.path} cx={CX} cy={CY} r={R} data-testid="orbit" />
        <circle className={styles.ball} cx={CX} cy={CY} r={3.5} />
        <line className={styles.guide} x1={CX} y1={CY} x2={CX + R} y2={CY} />
        <text className={styles.label} x={CX + R / 2} y={CY - 10} textAnchor="middle">
          r
        </text>
        <text className={styles.label} x={CX + R + 14} y={CY + 5}>
          r = {r} m
        </text>

        {/* the particle, shown at one point on its path */}
        <circle className={styles.particle} cx={CX} cy={CY - R} r={8} />
        <text className={styles.label} x={CX} y={CY - R - 16} textAnchor="middle">
          q
        </text>
      </svg>

      <p className={styles.legend}>
        <span>
          <var>r</var> = {r} m
        </span>
        <span>
          <var>T</var> = {T} s (one full loop)
        </span>
        <span>
          <var>v</var> = {v} m/s
        </span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. The circle is not to scale. The problem does not say
        which way the field points, so the drawing does not show which way the particle goes around.
      </figcaption>
    </figure>
  );
}
