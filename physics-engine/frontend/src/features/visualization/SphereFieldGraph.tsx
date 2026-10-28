import { useId } from "react";
import { formatValue } from "../../utils/format.ts";
import { fieldAt, type SphereData } from "./sphere.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 320;
const LEFT = 64;
const RIGHT = 32;
const TOP = 40;
const BOTTOM = 52;
const HEADROOM = 22;

/**
 * Field strength against distance from the centre of a uniformly charged sphere,
 * drawn from the verified answer. The curve rises in a straight line inside the
 * sphere and falls off outside it. Only R (as read) and the two solved points are
 * printed; the peak value at r = R is not, because that number would be frontend
 * arithmetic.
 */
export function SphereFieldGraph({ data }: { data: SphereData }) {
  const uid = useId().replace(/:/g, "");
  const head = `${uid}-axis`;

  const plotW = W - LEFT - RIGHT;
  const plotH = H - TOP - BOTTOM;
  const baseY = TOP + plotH;
  const rMax = Math.max(data.rOut * 1.25, data.R * 2);
  const peak = fieldAt(data.R, data);
  const sx = (r: number) => LEFT + (r / rMax) * plotW;
  const sy = (e: number) => baseY - (e / peak) * (plotH - HEADROOM);

  const path = Array.from({ length: 161 }, (_, i) => {
    const r = (i / 160) * rMax;
    return `${i === 0 ? "M" : "L"}${sx(r).toFixed(1)},${sy(fieldAt(r, data)).toFixed(1)}`;
  }).join(" ");

  const R = formatValue(data.R);
  const rIn = formatValue(data.rIn);
  const rOut = formatValue(data.rOut);
  const Ein = formatValue(data.Ein);
  const Eout = formatValue(data.Eout);
  const summary =
    `Field of a charged sphere of radius ${R} m: inside, the field grows steadily with distance ` +
    `from the centre; outside, it falls off. At r = ${rIn} m (inside) E = ${Ein} N/C. ` +
    `At r = ${rOut} m (outside) E = ${Eout} N/C.`;

  const pIn = { x: sx(data.rIn), y: sy(data.Ein) };
  const pOut = { x: sx(data.rOut), y: sy(data.Eout) };

  return (
    <figure className={styles.figure}>
      <svg viewBox={`0 0 ${W} ${H}`} className={styles.svg} role="img" aria-label={summary}>
        <defs>
          <marker
            id={head}
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path className={styles.plainHead} d="M0,0 L10,5 L0,10 z" />
          </marker>
        </defs>

        {/* inside the sphere */}
        <rect
          className={styles.area}
          x={LEFT}
          y={TOP}
          width={sx(data.R) - LEFT}
          height={plotH}
          data-testid="inside-region"
        />
        <text className={styles.rowTitle} x={(LEFT + sx(data.R)) / 2} y={TOP + 18} textAnchor="middle">
          inside
        </text>
        <text className={styles.rowTitle} x={sx(data.R) + 12} y={TOP + 18}>
          outside
        </text>

        {/* axes */}
        <line
          className={styles.axis}
          x1={LEFT}
          y1={baseY}
          x2={W - RIGHT + 16}
          y2={baseY}
          markerEnd={`url(#${head})`}
        />
        <line
          className={styles.axis}
          x1={LEFT}
          y1={baseY}
          x2={LEFT}
          y2={TOP - 12}
          markerEnd={`url(#${head})`}
        />
        <text className={styles.label} x={W - RIGHT + 12} y={H - 10} textAnchor="end">
          distance from centre r
        </text>
        <text className={styles.label} x={LEFT + 10} y={TOP - 8}>
          field E
        </text>
        <text className={styles.label} x={LEFT} y={baseY + 22} textAnchor="middle">
          0
        </text>
        <line className={styles.guide} x1={sx(data.R)} y1={TOP} x2={sx(data.R)} y2={baseY} />
        <text className={styles.label} x={sx(data.R)} y={baseY + 22} textAnchor="middle">
          R = {R} m
        </text>

        {/* field curve (shape only) */}
        <path className={styles.path} d={path} data-testid="field-curve" />

        {/* the two solved points */}
        <circle className={styles.ball} cx={pIn.x} cy={pIn.y} r={5} data-testid="point-in" />
        <text className={styles.label} x={pIn.x - 12} y={pIn.y - 8} textAnchor="end">
          A
        </text>
        <circle className={styles.ball} cx={pOut.x} cy={pOut.y} r={5} data-testid="point-out" />
        <text className={styles.label} x={pOut.x} y={pOut.y - 14} textAnchor="middle">
          B
        </text>
      </svg>

      <p className={styles.legend}>
        <span>
          A, inside (<var>r</var> = {rIn} m): <var>E</var> = {Ein} N/C
        </span>
        <span>
          B, outside (<var>r</var> = {rOut} m): <var>E</var> = {Eout} N/C
        </span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. The curve shows the shape of the field: a straight
        rise inside the sphere, then a fall-off outside. Only R and the marked points A and B
        are numbers from the engine.
      </figcaption>
    </figure>
  );
}