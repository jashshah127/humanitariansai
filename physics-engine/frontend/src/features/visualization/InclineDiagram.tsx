import { useId } from "react";
import { formatValue } from "../../utils/format.ts";
import type { InclineData } from "./incline.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 400;
const BASE_Y = 360;
const LEFT_X = 50;
const MAX_RUN = 470; // max width of the slope
const MAX_RISE = 260; // max height of the slope
const BLOCK = 46;
const ALONG = 0.38; // where the block sits, as a fraction of the slope from the top
const MG_LEN = 140; // px for the weight; other forces are drawn relative to it
const A_ARROW = 56; // acceleration arrow: fixed length, direction only

type Pt = { x: number; y: number };
const add = (p: Pt, q: Pt, k = 1): Pt => ({ x: p.x + k * q.x, y: p.y + k * q.y });

/**
 * Free-body diagram for a block sliding down a slope, drawn from the verified
 * answer. The problem gives no mass, so forces are labelled mg, N and f, not
 * numbered. Their lengths are to scale with each other: N = mg·cosθ, f = μ·N.
 */
export function InclineDiagram({ data }: { data: InclineData }) {
  const uid = useId().replace(/:/g, "");
  const forceHead = `${uid}-force`;
  const plainHead = `${uid}-plain`;

  const th = (data.thetaDeg * Math.PI) / 180;
  const cos = Math.cos(th);
  const sin = Math.sin(th);
  const slope = Math.min(MAX_RUN / cos, MAX_RISE / sin);

  // SVG y points down. u runs down the slope; n points out of the slope surface.
  const u: Pt = { x: cos, y: sin };
  const n: Pt = { x: sin, y: -cos };
  const top: Pt = { x: LEFT_X, y: BASE_Y - slope * sin };
  const corner: Pt = { x: LEFT_X, y: BASE_Y };
  const foot: Pt = { x: LEFT_X + slope * cos, y: BASE_Y };

  const contact = add(top, u, ALONG * slope);
  const centre = add(contact, n, BLOCK / 2);
  const upFace = add(centre, u, -BLOCK / 2);

  const nLen = MG_LEN * cos;
  const fLen = MG_LEN * data.mu * cos;
  const mgEnd: Pt = { x: centre.x, y: centre.y + MG_LEN };
  const nEnd = add(centre, n, nLen);
  const fEnd = add(upFace, u, -fLen);
  const aMid = add(add(contact, u, BLOCK * 1.9), n, BLOCK * 0.7); // beside the block, downhill
  const aStart = add(aMid, u, -A_ARROW / 2);
  const aEnd = add(aMid, u, A_ARROW / 2);

  const arcR = 46;
  const arcEnd = add(foot, { x: -cos, y: -sin }, arcR);
  const angLabel = add(foot, { x: -Math.cos(th / 2), y: -Math.sin(th / 2) }, arcR + 18);

  const thetaDeg = formatValue(data.thetaDeg);
  const mu = formatValue(data.mu);
  const a = formatValue(data.a);
  const v = formatValue(data.v);
  const d = formatValue(data.d);
  const friction = data.mu > 0;
  const summary =
    `Block on a ${thetaDeg}° slope with friction coefficient ${mu}. ` +
    `Forces: weight mg straight down, normal force N out of the slope` +
    (friction ? ", friction f up the slope. " : ", no friction. ") +
    `It accelerates down the slope at ${a} m/s² and reaches ${v} m/s after ${d} m.`;

  const pts = (...p: Pt[]) => p.map((q) => `${q.x.toFixed(1)},${q.y.toFixed(1)}`).join(" ");

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

        {/* the slope */}
        <polygon className={styles.slope} points={pts(top, corner, foot)} />
        <path
          className={styles.axis}
          d={`M${foot.x - arcR},${foot.y} A${arcR},${arcR} 0 0 1 ${arcEnd.x},${arcEnd.y}`}
          fill="none"
        />
        <text className={styles.label} x={angLabel.x} y={angLabel.y + 5} textAnchor="end">
          θ = {thetaDeg}°
        </text>

        {/* the block, sitting on the slope */}
        <g transform={`translate(${contact.x} ${contact.y}) rotate(${data.thetaDeg})`}>
          <rect
            className={styles.box}
            x={-BLOCK / 2}
            y={-BLOCK}
            width={BLOCK}
            height={BLOCK}
            rx={3}
          />
        </g>

        {/* weight: straight down */}
        <line
          className={styles.weight}
          data-testid="force-mg"
          x1={centre.x}
          y1={centre.y}
          x2={mgEnd.x}
          y2={mgEnd.y}
          markerEnd={`url(#${plainHead})`}
        />
        <text className={styles.label} x={mgEnd.x + 10} y={mgEnd.y}>
          mg
        </text>

        {/* normal force: out of the slope */}
        <line
          className={styles.force}
          data-testid="force-N"
          x1={centre.x}
          y1={centre.y}
          x2={nEnd.x}
          y2={nEnd.y}
          markerEnd={`url(#${forceHead})`}
        />
        <text className={styles.label} x={nEnd.x + 8} y={nEnd.y - 6}>
          N
        </text>

        {/* friction: up the slope, from the block's uphill face */}
        {friction && (
          <>
            <line
              className={styles.force}
              data-testid="force-f"
              x1={upFace.x}
              y1={upFace.y}
              x2={fEnd.x}
              y2={fEnd.y}
              markerEnd={`url(#${forceHead})`}
            />
            <text className={styles.label} x={fEnd.x - 8} y={fEnd.y - 8} textAnchor="end">
              f
            </text>
          </>
        )}

        {/* acceleration: direction only */}
        <line
          className={styles.accel}
          data-testid="accel"
          x1={aStart.x}
          y1={aStart.y}
          x2={aEnd.x}
          y2={aEnd.y}
          markerEnd={`url(#${plainHead})`}
        />
        <text className={styles.label} x={aEnd.x + 8} y={aEnd.y - 4}>
          a
        </text>
      </svg>

      <p className={styles.legend}>
        <span>
          <var>a</var> = {a} m/s² down the slope
        </span>
        <span>
          <var>v</var> = {v} m/s after sliding {d} m from rest
        </span>
        <span>
          <var>μ</var> = {mu}
        </span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. The mass is not given, so forces are labelled, not
        numbered. Their lengths are to scale with each other. The dashed arrow shows only the
        direction of acceleration.
      </figcaption>
    </figure>
  );
}
