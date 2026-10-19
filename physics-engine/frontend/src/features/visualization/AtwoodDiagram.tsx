import { useId } from "react";
import { formatValue } from "../../utils/format.ts";
import { motion, type AtwoodData } from "./atwood.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 440;
const PULLEY = { x: 300, y: 70, r: 36 };
const BOX_TOP = 230;
const MAX_ARROW = 110; // px for the largest force; all force arrows share one scale
const A_ARROW = 56; // acceleration arrows: fixed length, they show direction only

/**
 * Free-body diagram for the Atwood machine, drawn from the verified answer.
 * Printed numbers are engine values only (T, a, and the masses as read). Weights
 * are labelled m₁g / m₂g, not with a number, because that number would be
 * frontend arithmetic rather than a verified result.
 */
export function AtwoodDiagram({ data }: { data: AtwoodData }) {
  // useId gives ":r1:"; colons break url(#...) references, so strip them.
  const uid = useId().replace(/:/g, "");
  const forceHead = `${uid}-force`;
  const plainHead = `${uid}-plain`;

  const w1 = data.m1 * data.g;
  const w2 = data.m2 * data.g;
  const scale = MAX_ARROW / Math.max(w1, w2, data.T);
  const heavier = Math.max(data.m1, data.m2);
  const side = (m: number) => 56 + 30 * (m / heavier);

  const dir = motion(data);
  const left = { x: PULLEY.x - PULLEY.r, s: side(data.m1), m: data.m1, w: w1, n: "1" };
  const right = { x: PULLEY.x + PULLEY.r, s: side(data.m2), m: data.m2, w: w2, n: "2" };

  const T = formatValue(data.T);
  const aAbs = formatValue(Math.abs(data.a));
  const moving =
    dir === "none"
      ? "The masses are equal, so neither accelerates."
      : `m${dir === "m2_down" ? "2" : "1"} accelerates down and m${dir === "m2_down" ? "1" : "2"} up at ${aAbs} m/s².`;
  const summary =
    `Atwood machine: m1 = ${formatValue(data.m1)} kg, m2 = ${formatValue(data.m2)} kg. ` +
    `Tension ${T} N on both sides. ${moving}`;

  function mass(b: typeof left, isLeft: boolean) {
    const top = BOX_TOP;
    const bottom = top + b.s;
    const mid = top + b.s / 2;
    const tLen = data.T * scale;
    const wLen = b.w * scale;
    const goesDown = (dir === "m2_down" && !isLeft) || (dir === "m1_down" && isLeft);
    const aX = isLeft ? b.x - b.s / 2 - 26 : b.x + b.s / 2 + 26;
    const labelX = isLeft ? b.x - 12 : b.x + 12;
    const anchor = isLeft ? "end" : "start";

    return (
      <g>
        {/* string from the pulley to the box */}
        <line className={styles.string} x1={b.x} y1={PULLEY.y} x2={b.x} y2={top} />
        {/* tension: up, along the string */}
        <line
          className={styles.force}
          x1={b.x}
          y1={top}
          x2={b.x}
          y2={top - tLen}
          markerEnd={`url(#${forceHead})`}
        />
        <text className={styles.label} x={labelX} y={top - tLen / 2} textAnchor={anchor}>
          T = {T} N
        </text>
        {/* the mass */}
        <rect className={styles.box} x={b.x - b.s / 2} y={top} width={b.s} height={b.s} rx={4} />
        <text className={styles.label} x={b.x} y={mid - 4} textAnchor="middle">
          m{b.n === "1" ? "₁" : "₂"}
        </text>
        <text className={styles.label} x={b.x} y={mid + 14} textAnchor="middle">
          {formatValue(b.m)} kg
        </text>
        {/* weight: down */}
        <line
          className={styles.weight}
          x1={b.x}
          y1={bottom}
          x2={b.x}
          y2={bottom + wLen}
          markerEnd={`url(#${plainHead})`}
        />
        <text className={styles.label} x={labelX} y={bottom + wLen / 2 + 5} textAnchor={anchor}>
          m{b.n === "1" ? "₁" : "₂"}g
        </text>
        {/* acceleration: direction only */}
        {dir !== "none" && (
          <line
            className={styles.accel}
            data-testid={`accel-m${b.n}`}
            data-direction={goesDown ? "down" : "up"}
            x1={aX}
            y1={goesDown ? mid - A_ARROW / 2 : mid + A_ARROW / 2}
            x2={aX}
            y2={goesDown ? mid + A_ARROW / 2 : mid - A_ARROW / 2}
            markerEnd={`url(#${plainHead})`}
          />
        )}
      </g>
    );
  }

  return (
    <figure className={styles.figure}>
      <svg viewBox={`0 0 ${W} ${H}`} className={styles.svg} role="img" aria-label={summary}>
        <defs>
          <marker
            id={forceHead}
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path className={styles.forceHead} d="M0,0 L10,5 L0,10 z" />
          </marker>
          <marker
            id={plainHead}
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
        {/* ceiling and pulley */}
        <line className={styles.ground} x1={PULLEY.x - 60} y1={18} x2={PULLEY.x + 60} y2={18} />
        <line className={styles.string} x1={PULLEY.x} y1={18} x2={PULLEY.x} y2={PULLEY.y} />
        <circle className={styles.pulley} cx={PULLEY.x} cy={PULLEY.y} r={PULLEY.r} />
        {mass(left, true)}
        {mass(right, false)}
      </svg>

      <p className={styles.legend}>
        <span>
          <var>T</var> = {T} N on both sides (one massless string)
        </span>
        <span>
          <var>a</var> = {aAbs} m/s²
          {dir === "none" ? " (balanced)" : ` (m${dir === "m2_down" ? "₂" : "₁"} moves down)`}
        </span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. Force arrows are to scale with each other; dashed
        arrows show only the direction of acceleration.
      </figcaption>
    </figure>
  );
}
