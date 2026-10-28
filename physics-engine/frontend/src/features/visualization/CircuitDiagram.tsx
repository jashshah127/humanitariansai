import { useId } from "react";
import { formatValue } from "../../utils/format.ts";
import type { CircuitData } from "./circuit.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 360;
const XB = 100; // battery
const X1 = 310; // branch 1: R1 then R2
const X2 = 480; // branch 2: R3
const YT = 60; // top wire
const YB = 300; // bottom wire

/** Zigzag resistor drawn vertically from y1 to y2. */
function zigzag(x: number, y1: number, y2: number): string {
  const segs = 6;
  const step = (y2 - y1) / segs;
  const pts = [`M${x},${y1}`];
  for (let i = 0; i < segs; i++)
    pts.push(`L${x + (i % 2 === 0 ? 10 : -10)},${y1 + step * (i + 0.5)}`);
  pts.push(`L${x},${y2}`);
  return pts.join(" ");
}

/**
 * Circuit drawing for "R1 and R2 in series, that pair in parallel with R3",
 * drawn from the verified answer. The layout is fixed because the card only
 * covers this one layout. Printed numbers are engine values only.
 */
export function CircuitDiagram({ data }: { data: CircuitData }) {
  const uid = useId().replace(/:/g, "");
  const head = `${uid}-i`;

  const R1 = formatValue(data.R1);
  const R2 = formatValue(data.R2);
  const R3 = formatValue(data.R3);
  const V = formatValue(data.V);
  const It = formatValue(data.It);
  const I1 = formatValue(data.I1);
  const I2 = formatValue(data.I2);
  const summary =
    `Circuit: R1 = ${R1} Ω and R2 = ${R2} Ω in series, that pair in parallel with R3 = ${R3} Ω, ` +
    `across a ${V} V source. The total current of ${It} A splits into ${I1} A through R1 and R2, ` +
    `and ${I2} A through R3.`;

  const arrow = (x1: number, y1: number, x2: number, y2: number, id: string) => (
    <line
      className={styles.current}
      data-testid={id}
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      markerEnd={`url(#${head})`}
    />
  );

  return (
    <figure className={styles.figure}>
      <svg viewBox={`0 0 ${W} ${H}`} className={styles.svg} role="img" aria-label={summary}>
        <defs>
          <marker
            id={head}
            viewBox="0 0 10 10"
            refX="5"
            refY="5"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path className={styles.forceHead} d="M0,0 L10,5 L0,10 z" />
          </marker>
        </defs>

        {/* top and bottom wires */}
        <line className={styles.wire} x1={XB} y1={YT} x2={X2} y2={YT} />
        <line className={styles.wire} x1={XB} y1={YB} x2={X2} y2={YB} />

        {/* source: long plate is + */}
        <line className={styles.wire} x1={XB} y1={YT} x2={XB} y2={170} />
        <line className={styles.plate} x1={XB - 22} y1={170} x2={XB + 22} y2={170} />
        <line className={styles.plate} x1={XB - 12} y1={184} x2={XB + 12} y2={184} />
        <line className={styles.wire} x1={XB} y1={184} x2={XB} y2={YB} />
        <text className={styles.label} x={XB + 30} y={166}>
          +
        </text>
        <text className={styles.label} x={XB - 32} y={182} textAnchor="end">
          V = {V} V
        </text>

        {/* branch 1: R1 and R2 in series */}
        <line className={styles.wire} x1={X1} y1={YT} x2={X1} y2={92} />
        <path className={styles.wire} d={zigzag(X1, 92, 152)} />
        <line className={styles.wire} x1={X1} y1={152} x2={X1} y2={208} />
        <path className={styles.wire} d={zigzag(X1, 208, 268)} />
        <line className={styles.wire} x1={X1} y1={268} x2={X1} y2={YB} />
        <text className={styles.label} x={X1 - 20} y={127} textAnchor="end">
          R₁ = {R1} Ω
        </text>
        <text className={styles.label} x={X1 - 20} y={243} textAnchor="end">
          R₂ = {R2} Ω
        </text>

        {/* branch 2: R3 */}
        <line className={styles.wire} x1={X2} y1={YT} x2={X2} y2={150} />
        <path className={styles.wire} d={zigzag(X2, 150, 210)} />
        <line className={styles.wire} x1={X2} y1={210} x2={X2} y2={YB} />
        <text className={styles.label} x={X2 + 20} y={185}>
          R₃ = {R3} Ω
        </text>

        {/* junctions */}
        <circle className={styles.ball} cx={X1} cy={YT} r={4} />
        <circle className={styles.ball} cx={X1} cy={YB} r={4} />

        {/* conventional current, out of the + side */}
        {arrow(190, YT, 214, YT, "i-total")}
        <text className={styles.label} x={202} y={YT - 14} textAnchor="middle">
          I = {It} A
        </text>
        {arrow(X1, 168, X1, 192, "i-branch1")}
        <text className={styles.label} x={X1 + 16} y={186}>
          I₁ = {I1} A
        </text>
        {arrow(X2, 92, X2, 116, "i-branch2")}
        <text className={styles.label} x={X2 + 16} y={110}>
          I₂ = {I2} A
        </text>
      </svg>

      <p className={styles.legend}>
        <span>R₁ + R₂ = {formatValue(data.Rs)} Ω</span>
        <span>
          <var>R</var>
          <sub>eq</sub> = {formatValue(data.Req)} Ω
        </span>
        <span>
          {I1} A + {I2} A = {It} A
        </span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. Arrows show conventional current, leaving the + side
        of the source.
      </figcaption>
    </figure>
  );
}
