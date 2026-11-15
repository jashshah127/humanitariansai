import { useId } from "react";
import { formatValue } from "../../utils/format.ts";
import type { DiskData } from "./disk.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 320;
const DCX = 140;
const DCY = 160;
const DR = 100; // disk drawn at a fixed size; its real radius is labelled
const GX0 = 310; // graph box
const GX1 = 570;
const GY0 = 60;
const GY1 = 260;

/**
 * Solid disk under a constant torque, drawn from the verified answer: the disk,
 * and its spin rate growing in a straight line from rest. The problem gives no
 * direction of turning, so none is shown.
 */
export function DiskDiagram({ data }: { data: DiskData }) {
  const uid = useId().replace(/:/g, "");
  const head = `${uid}-axis`;

  const M = formatValue(data.M);
  const R = formatValue(data.R);
  const tau = formatValue(data.tau);
  const t = formatValue(data.t);
  const I = formatValue(data.I);
  const alpha = formatValue(data.alpha);
  const omega = formatValue(data.omega);
  const summary =
    `Solid disk, mass ${M} kg and radius ${R} m, with a constant torque of ${tau} N·m. ` +
    `Moment of inertia ${I} kg·m², angular acceleration ${alpha} rad/s². ` +
    `Starting from rest, its spin rate grows steadily to ${omega} rad/s after ${t} s.`;

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

        {/* the disk */}
        <circle className={styles.planet} cx={DCX} cy={DCY} r={DR} data-testid="disk" />
        <circle className={styles.ball} cx={DCX} cy={DCY} r={4} />
        <line className={styles.guide} x1={DCX} y1={DCY} x2={DCX + DR} y2={DCY} />
        <text className={styles.label} x={DCX + DR / 2} y={DCY - 10} textAnchor="middle">
          R = {R} m
        </text>
        <text className={styles.label} x={DCX} y={DCY + 34} textAnchor="middle">
          M = {M} kg
        </text>
        <text className={styles.label} x={DCX} y={DCY + DR + 30} textAnchor="middle">
          torque = {tau} N·m
        </text>

        {/* spin rate over time, from rest */}
        <line
          className={styles.axis}
          x1={GX0}
          y1={GY1}
          x2={GX1}
          y2={GY1}
          markerEnd={`url(#${head})`}
        />
        <line
          className={styles.axis}
          x1={GX0}
          y1={GY1}
          x2={GX0}
          y2={GY0 - 10}
          markerEnd={`url(#${head})`}
        />
        <text className={styles.label} x={GX0 + 8} y={GY0 - 14}>
          spin rate ω (rad/s)
        </text>
        <text className={styles.label} x={GX1} y={GY1 + 40} textAnchor="end">
          time (s)
        </text>
        <text className={styles.label} x={GX0} y={GY1 + 20} textAnchor="middle">
          0
        </text>
        <text className={styles.label} x={GX1 - 20} y={GY1 + 20} textAnchor="middle">
          {t}
        </text>
        <line
          className={styles.path}
          data-testid="omega-line"
          x1={GX0}
          y1={GY1}
          x2={GX1 - 20}
          y2={GY0 + 20}
        />
        <line className={styles.guide} x1={GX1 - 20} y1={GY0 + 20} x2={GX1 - 20} y2={GY1} />
        <circle className={styles.ball} cx={GX1 - 20} cy={GY0 + 20} r={4} />
        <text className={styles.label} x={GX1 - 28} y={GY0 + 12} textAnchor="end">
          ω = {omega} rad/s
        </text>
      </svg>

      <p className={styles.legend}>
        <span>
          <var>I</var> = {I} kg·m²
        </span>
        <span>
          <var>α</var> = {alpha} rad/s² (the slope of the line)
        </span>
        <span>
          <var>ω</var> = {omega} rad/s after {t} s
        </span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. The disk is not to scale. The problem does not say
        which way the torque turns the disk, so no direction is shown.
      </figcaption>
    </figure>
  );
}
