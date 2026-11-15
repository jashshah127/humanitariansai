import { useId } from "react";
import { formatValue } from "../../utils/format.ts";
import type { KinematicsData } from "./kinematics.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 320;
const LEFT = 104; // room for the v₀ label left of the axis
const RIGHT = 40;
const TOP = 36;
const BOTTOM = 52;
const HEADROOM = 24; // px above the highest speed

/**
 * Speed-over-time graph for constant acceleration, drawn from the verified answer.
 * The shaded area under the line is the distance travelled, which is the point a
 * student should take away. Printed numbers are engine values only (v0, t as read;
 * v and s as solved).
 */
export function SpeedTimeGraph({ data }: { data: KinematicsData }) {
  const uid = useId().replace(/:/g, "");
  const head = `${uid}-axis`;

  const plotW = W - LEFT - RIGHT;
  const plotH = H - TOP - BOTTOM;
  const baseY = TOP + plotH;
  const vMax = Math.max(data.v0, data.v);
  const sx = (t: number) => LEFT + (t / data.t) * plotW;
  const sy = (v: number) => baseY - (v / vMax) * (plotH - HEADROOM);

  const x0 = sx(0);
  const x1 = sx(data.t);
  const y0 = sy(data.v0);
  const y1 = sy(data.v);

  const v0 = formatValue(data.v0);
  const v = formatValue(data.v);
  const t = formatValue(data.t);
  const s = formatValue(data.s);
  const a = formatValue(data.a);
  const summary =
    `Speed over time: the speed changes steadily from ${v0} m/s to ${v} m/s over ${t} s. ` +
    `The shaded area under the line is the distance travelled, ${s} m.`;

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

        {/* distance = area under the line */}
        <polygon
          className={styles.area}
          data-testid="distance-area"
          points={`${x0},${baseY} ${x0},${y0} ${x1},${y1} ${x1},${baseY}`}
        />
        <text className={styles.label} x={(x0 + x1) / 2} y={baseY - 18} textAnchor="middle">
          area = distance = {s} m
        </text>

        {/* axes */}
        <line
          className={styles.axis}
          x1={LEFT}
          y1={baseY}
          x2={W - RIGHT + 24}
          y2={baseY}
          markerEnd={`url(#${head})`}
        />
        <line
          className={styles.axis}
          x1={LEFT}
          y1={baseY}
          x2={LEFT}
          y2={TOP - 10}
          markerEnd={`url(#${head})`}
        />
        <text className={styles.label} x={W - RIGHT + 20} y={H - 10} textAnchor="end">
          time (s)
        </text>
        <text className={styles.label} x={LEFT + 10} y={TOP - 4}>
          speed (m/s)
        </text>
        <text className={styles.label} x={LEFT} y={baseY + 22} textAnchor="middle">
          0
        </text>
        <text className={styles.label} x={x1} y={baseY + 22} textAnchor="middle">
          {t}
        </text>

        {/* the speed line */}
        <line className={styles.path} data-testid="speed-line" x1={x0} y1={y0} x2={x1} y2={y1} />
        <line className={styles.guide} x1={x1} y1={y1} x2={x1} y2={baseY} />
        <circle className={styles.ball} cx={x0} cy={y0} r={4} />
        <circle className={styles.ball} cx={x1} cy={y1} r={4} />
        <text className={styles.label} x={LEFT - 10} y={y0 + 5} textAnchor="end">
          v₀ = {v0} m/s
        </text>
        <text className={styles.label} x={x1 - 8} y={y1 - 12} textAnchor="end">
          v = {v} m/s
        </text>
      </svg>

      <p className={styles.legend}>
        <span>
          <var>v</var> = {v} m/s after {t} s
        </span>
        <span>
          <var>s</var> = {s} m
        </span>
        <span>
          <var>a</var> = {a} m/s² (the slope of the line)
        </span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. Steady acceleration gives a straight line; the shaded
        area under it is the distance travelled.
      </figcaption>
    </figure>
  );
}
