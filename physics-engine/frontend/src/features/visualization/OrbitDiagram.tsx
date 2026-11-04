import { formatValue } from "../../utils/format.ts";
import type { OrbitData } from "./orbit.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 360;
const CX = 230;
const CY = 180;
const ORBIT_PX = 140; // the orbit is always this size; the body is scaled to match
const MIN_BODY_PX = 10;

/**
 * Circular orbit, drawn from the verified answer. The central body and the orbit
 * are to scale with each other (a low orbit hugs the surface), unless the body
 * would be too small to see, in which case the caption says so. The problem gives
 * no direction of travel, so none is shown.
 */
export function OrbitDiagram({ data }: { data: OrbitData }) {
  const exact = (ORBIT_PX * data.Re) / data.r;
  const bodyPx = Math.max(MIN_BODY_PX, exact);
  const toScale = exact >= MIN_BODY_PX;

  const r = formatValue(data.r);
  const h = formatValue(data.h);
  const Re = formatValue(data.Re);
  const v = formatValue(data.v);
  const T = formatValue(data.T);
  const summary =
    `Circular orbit at altitude h = ${h} m above a body of radius ${Re} m, so the orbit radius ` +
    `is r = ${r} m from the centre. Orbital speed ${v} m/s; one orbit takes ${T} s.`;

  return (
    <figure className={styles.figure}>
      <svg viewBox={`0 0 ${W} ${H}`} className={styles.svg} role="img" aria-label={summary}>
        <circle className={styles.planet} cx={CX} cy={CY} r={bodyPx} data-testid="body" />
        <circle className={styles.path} cx={CX} cy={CY} r={ORBIT_PX} data-testid="orbit" />
        <circle className={styles.ball} cx={CX} cy={CY} r={3} />

        {/* r: centre to satellite */}
        <line className={styles.guide} x1={CX} y1={CY} x2={CX + ORBIT_PX} y2={CY} />
        <text className={styles.label} x={CX + ORBIT_PX / 2} y={CY + 22} textAnchor="middle">
          r
        </text>
        <circle className={styles.particle} cx={CX + ORBIT_PX} cy={CY} r={7} />

        {/* labels to the right */}
        <text className={styles.label} x={CX + ORBIT_PX + 24} y={CY - 30}>
          satellite
        </text>
        <text className={styles.label} x={CX + ORBIT_PX + 24} y={CY + 5}>
          r = {r} m
        </text>
        <text className={styles.label} x={CX + ORBIT_PX + 24} y={CY + 27}>
          = Re + h
        </text>
        <text
          className={styles.label}
          x={CX}
          y={bodyPx > 70 ? CY - 30 : CY - bodyPx - 10}
          textAnchor="middle"
        >
          Re = {Re} m
        </text>
      </svg>

      <p className={styles.legend}>
        <span>
          altitude <var>h</var> = {h} m
        </span>
        <span>
          <var>v</var> = {v} m/s
        </span>
        <span>
          <var>T</var> = {T} s (one orbit)
        </span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above.{" "}
        {toScale
          ? "The body and the orbit are to scale with each other."
          : "The body is drawn larger than to scale so it can be seen."}{" "}
        The problem gives no direction of travel, so none is shown.
      </figcaption>
    </figure>
  );
}
