import { formatValue } from "../../utils/format.ts";
import type { LoopData } from "./loop.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 320;
const CX = 250;
const CY = 165;
const LR = 105; // loop drawn at a fixed size; its real radius is labelled
const GAP_DEG = 12; // small gap in the loop where the EMF is measured

/**
 * Circular loop in a changing magnetic field, drawn from the verified answer.
 * The problem gives how fast the field changes but not which way it points or
 * whether it grows or shrinks in that direction, so the field has no into/out
 * symbols and no current direction is shown.
 */
export function LoopDiagram({ data }: { data: LoopData }) {
  const g = (GAP_DEG * Math.PI) / 180;
  const start = { x: CX + LR * Math.cos(g), y: CY - LR * Math.sin(g) };
  const end = { x: CX + LR * Math.cos(g), y: CY + LR * Math.sin(g) };

  const r = formatValue(data.r);
  const dBdt = formatValue(data.dBdt);
  const A = formatValue(data.A);
  const EMF = formatValue(data.EMF);
  const summary =
    `Circular loop of radius ${r} m, area ${A} m², in a magnetic field changing at ${dBdt} T/s. ` +
    `The induced EMF around the loop is ${EMF} V. ` +
    `Directions are not shown because the problem does not give them.`;

  return (
    <figure className={styles.figure}>
      <svg viewBox={`0 0 ${W} ${H}`} className={styles.svg} role="img" aria-label={summary}>
        {/* the region with the changing field */}
        <rect
          className={styles.area}
          x={110}
          y={30}
          width={280}
          height={270}
          rx={6}
          data-testid="field-region"
        />
        <text className={styles.label} x={118} y={52}>
          field changing at {dBdt} T/s
        </text>

        {/* the loop, with a small gap where the EMF appears */}
        <path
          className={styles.wireThick}
          data-testid="loop"
          fill="none"
          d={`M${start.x},${start.y} A${LR},${LR} 0 1 0 ${end.x},${end.y}`}
        />
        <circle className={styles.ball} cx={start.x} cy={start.y} r={4} />
        <circle className={styles.ball} cx={end.x} cy={end.y} r={4} />

        <circle className={styles.ball} cx={CX} cy={CY} r={3} />
        <line className={styles.guide} x1={CX} y1={CY} x2={CX} y2={CY + LR} />
        <text className={styles.label} x={CX + 8} y={CY + LR / 2}>
          r = {r} m
        </text>
        <text className={styles.label} x={CX} y={CY - 24} textAnchor="middle">
          area A = {A} m²
        </text>

        <text className={styles.label} x={start.x + 22} y={CY + 5}>
          EMF = {EMF} V
        </text>
      </svg>

      <p className={styles.legend}>
        <span>
          <var>A</var> = {A} m²
        </span>
        <span>EMF = {EMF} V</span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. The loop is not to scale. The problem does not say
        which way the field points, so the drawing shows no field symbols and no current direction.
        The field is taken to pass straight through the loop.
      </figcaption>
    </figure>
  );
}
