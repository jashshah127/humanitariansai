import { useId } from "react";
import { formatValue } from "../../utils/format.ts";
import type { CollisionData } from "./collision.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 400;
const X0 = 40;
const CART_H = 44;
const WHEEL_R = 7;
const FULL_W = 150; // px width for both carts together; each cart is its share by mass
const MIN_W = 36;
const V_MAX = 150; // px for the faster speed; both speed arrows share one scale
const BEFORE_Y = 130; // ground line, before
const AFTER_Y = 250; // ground line, after
const BAR_X = 150;
const BAR_MAX = 360; // px for KE before; both bars share one scale
const BAR_H = 18;

/**
 * Before/after picture of a perfectly inelastic collision, drawn from the
 * verified answer. Printed numbers are engine values only. The joined cart is
 * labelled m₁ + m₂ rather than with a number, because that sum would be
 * frontend arithmetic.
 */
export function CollisionDiagram({ data }: { data: CollisionData }) {
  const uid = useId().replace(/:/g, "");
  const head = `${uid}-v`;

  const total = data.m1 + data.m2;
  const w1 = Math.max(MIN_W, (FULL_W * data.m1) / total);
  const w2 = Math.max(MIN_W, (FULL_W * data.m2) / total);
  const v1Len = V_MAX;
  const vfLen = (V_MAX * data.vf) / data.v1;

  const cart2X = X0 + w1 + 8 + V_MAX + 40;
  const joinedX = cart2X - w1;
  const split = (FULL_W * data.m1) / total;

  const keAfterW = (BAR_MAX * data.KEf) / data.KEi;
  const lostW = BAR_MAX - keAfterW;

  const m1 = formatValue(data.m1);
  const m2 = formatValue(data.m2);
  const v1 = formatValue(data.v1);
  const vf = formatValue(data.vf);
  const KEi = formatValue(data.KEi);
  const KEf = formatValue(data.KEf);
  const dKE = formatValue(data.dKE);
  const summary =
    `Collision: a ${m1} kg cart moving at ${v1} m/s hits a ${m2} kg cart at rest and they stick. ` +
    `Together they move at ${vf} m/s. Kinetic energy goes from ${KEi} J to ${KEf} J, so ${dKE} J is lost.`;

  function cart(x: number, w: number, ground: number, top: string, bottom: string | null) {
    // An empty top label draws the cart body only; the caller adds its own labels.
    const y = ground - 2 * WHEEL_R - CART_H;
    return (
      <g>
        <rect className={styles.box} x={x} y={y} width={w} height={CART_H} rx={4} />
        <circle className={styles.wheel} cx={x + w * 0.25} cy={ground - WHEEL_R} r={WHEEL_R} />
        <circle className={styles.wheel} cx={x + w * 0.75} cy={ground - WHEEL_R} r={WHEEL_R} />
        {top && (
          <text
            className={styles.label}
            x={x + w / 2}
            y={y + (bottom ? 19 : 27)}
            textAnchor="middle"
          >
            {top}
          </text>
        )}
        {bottom && (
          <text className={styles.label} x={x + w / 2} y={y + 36} textAnchor="middle">
            {bottom}
          </text>
        )}
      </g>
    );
  }

  const mid = (ground: number) => ground - 2 * WHEEL_R - CART_H / 2;

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
            <path className={styles.forceHead} d="M0,0 L10,5 L0,10 z" />
          </marker>
        </defs>

        {/* before */}
        <text className={styles.rowTitle} x={X0} y={BEFORE_Y - 82}>
          Before
        </text>
        <line className={styles.ground} x1={16} y1={BEFORE_Y} x2={W - 16} y2={BEFORE_Y} />
        {cart(X0, w1, BEFORE_Y, "m₁", `${m1} kg`)}
        <line
          className={styles.force}
          data-testid="v-before"
          x1={X0 + w1 + 8}
          y1={mid(BEFORE_Y)}
          x2={X0 + w1 + 8 + v1Len}
          y2={mid(BEFORE_Y)}
          markerEnd={`url(#${head})`}
        />
        <text
          className={styles.label}
          x={X0 + w1 + 8 + v1Len / 2}
          y={mid(BEFORE_Y) - 12}
          textAnchor="middle"
        >
          v₁ = {v1} m/s
        </text>
        {cart(cart2X, w2, BEFORE_Y, "m₂", `${m2} kg`)}
        <text
          className={styles.label}
          x={cart2X + w2 / 2}
          y={BEFORE_Y - 2 * WHEEL_R - CART_H - 10}
          textAnchor="middle"
        >
          at rest
        </text>

        {/* after */}
        <text className={styles.rowTitle} x={X0} y={AFTER_Y - 82}>
          After (stuck together)
        </text>
        <line className={styles.ground} x1={16} y1={AFTER_Y} x2={W - 16} y2={AFTER_Y} />
        {cart(joinedX, FULL_W, AFTER_Y, "", null)}
        <line
          className={styles.guide}
          x1={joinedX + split}
          y1={AFTER_Y - 2 * WHEEL_R - CART_H}
          x2={joinedX + split}
          y2={AFTER_Y - 2 * WHEEL_R}
        />
        {split >= 30 && FULL_W - split >= 30 ? (
          <>
            <text
              className={styles.label}
              x={joinedX + split / 2}
              y={mid(AFTER_Y) + 5}
              textAnchor="middle"
            >
              m₁
            </text>
            <text
              className={styles.label}
              x={joinedX + split + (FULL_W - split) / 2}
              y={mid(AFTER_Y) + 5}
              textAnchor="middle"
            >
              m₂
            </text>
          </>
        ) : (
          <text
            className={styles.label}
            x={joinedX + FULL_W / 2}
            y={mid(AFTER_Y) - 30}
            textAnchor="middle"
          >
            m₁ + m₂
          </text>
        )}
        <line
          className={styles.force}
          data-testid="v-after"
          x1={joinedX + FULL_W + 8}
          y1={mid(AFTER_Y)}
          x2={joinedX + FULL_W + 8 + vfLen}
          y2={mid(AFTER_Y)}
          markerEnd={`url(#${head})`}
        />
        <text className={styles.label} x={joinedX + FULL_W + 8} y={mid(AFTER_Y) - 12}>
          v
          <tspan dy="4" fontSize="11">
            f
          </tspan>
          <tspan dy="-4">
            {"\u00a0"}= {vf} m/s
          </tspan>
        </text>

        {/* kinetic energy bars */}
        <text className={styles.rowTitle} x={X0} y={296}>
          Kinetic energy
        </text>
        <text className={styles.label} x={BAR_X - 10} y={322} textAnchor="end">
          before
        </text>
        <rect className={styles.bar} x={BAR_X} y={308} width={BAR_MAX} height={BAR_H} />
        <text className={styles.label} x={BAR_X + BAR_MAX + 8} y={322}>
          {KEi} J
        </text>
        <text className={styles.label} x={BAR_X - 10} y={358} textAnchor="end">
          after
        </text>
        <rect className={styles.bar} x={BAR_X} y={344} width={keAfterW} height={BAR_H} />
        <rect
          className={styles.barLost}
          data-testid="ke-lost"
          x={BAR_X + keAfterW}
          y={344}
          width={lostW}
          height={BAR_H}
        />
        <text className={styles.label} x={BAR_X + BAR_MAX + 8} y={358}>
          {KEf} J
        </text>
        <text className={styles.label} x={BAR_X + BAR_MAX} y={386} textAnchor="end">
          dashed part: {dKE} J lost
        </text>
      </svg>

      <p className={styles.legend}>
        <span>
          <var>v</var>
          <sub>f</sub> = {vf} m/s
        </span>
        <span>KE before = {KEi} J</span>
        <span>KE after = {KEf} J</span>
        <span>KE lost = {dKE} J</span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. Speed arrows are to scale with each other, and so are
        the energy bars. Cart widths show each cart&apos;s share of the total mass.
      </figcaption>
    </figure>
  );
}
