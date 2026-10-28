import { useId } from "react";
import { formatValue } from "../../utils/format.ts";
import { chargeAt, type RcData } from "./rc.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 320;
const LEFT = 64;
const RIGHT = 28;
const TOP = 36;
const BOTTOM = 52;
const SPANS = 5; // the time axis runs to 5 time constants
const HEADROOM = 18; // px between the V0 line and the top of the plot

/**
 * Capacitor charging curve, drawn from the verified answer. Printed numbers are
 * engine values only (V0 as read, tau, Vc). Time ticks are labelled τ, 2τ, ...
 * rather than with seconds, because those seconds would be frontend arithmetic.
 */
export function RcCurve({ data }: { data: RcData }) {
  const uid = useId().replace(/:/g, "");
  const head = `${uid}-axis`;

  const plotW = W - LEFT - RIGHT;
  const plotH = H - TOP - BOTTOM;
  const baseY = TOP + plotH;
  const tMax = SPANS * data.tau;
  const sx = (t: number) => LEFT + (t / tMax) * plotW;
  const sy = (v: number) => baseY - (v / data.V0) * (plotH - HEADROOM);

  const path = Array.from({ length: 121 }, (_, i) => {
    const t = (i / 120) * tMax;
    return `${i === 0 ? "M" : "L"}${sx(t).toFixed(1)},${sy(chargeAt(t, data)).toFixed(1)}`;
  }).join(" ");

  const V0 = formatValue(data.V0);
  const Vc = formatValue(data.Vc);
  const tau = formatValue(data.tau);
  const px = sx(data.tau);
  const py = sy(data.Vc);
  const summary =
    `RC charging: the capacitor voltage starts at 0 and rises toward V0 = ${V0} V. ` +
    `At one time constant, τ = ${tau} s, it is ${Vc} V.`;

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

        {/* axes */}
        <line
          className={styles.axis}
          x1={LEFT}
          y1={baseY}
          x2={W - RIGHT + 10}
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
        {Array.from({ length: SPANS + 1 }, (_, n) => (
          <g key={n}>
            <line
              className={styles.axis}
              x1={sx(n * data.tau)}
              y1={baseY}
              x2={sx(n * data.tau)}
              y2={baseY + 6}
            />
            <text className={styles.label} x={sx(n * data.tau)} y={baseY + 24} textAnchor="middle">
              {n === 0 ? "0" : n === 1 ? "τ" : `${n}τ`}
            </text>
          </g>
        ))}
        <text className={styles.label} x={W - RIGHT} y={H - 6} textAnchor="end">
          time
        </text>
        <text className={styles.label} x={LEFT + 10} y={TOP - 6}>
          Vc
        </text>
        <text className={styles.label} x={LEFT - 10} y={baseY + 5} textAnchor="end">
          0
        </text>
        <text className={styles.label} x={LEFT - 10} y={sy(data.V0) + 5} textAnchor="end">
          V₀
        </text>

        {/* the voltage the capacitor approaches */}
        <line className={styles.guide} x1={LEFT} y1={sy(data.V0)} x2={W - RIGHT} y2={sy(data.V0)} />
        <text className={styles.label} x={W - RIGHT} y={sy(data.V0) - 8} textAnchor="end">
          V₀ = {V0} V
        </text>

        {/* the charging curve (shape only) */}
        <path className={styles.path} d={path} data-testid="rc-curve" />

        {/* the solved point: Vc at t = tau */}
        <line className={styles.guide} x1={px} y1={py} x2={px} y2={baseY} />
        <line className={styles.guide} x1={LEFT} y1={py} x2={px} y2={py} />
        <circle className={styles.ball} cx={px} cy={py} r={5} data-testid="rc-point" />
        <text className={styles.label} x={px + 12} y={py + 20}>
          Vc = {Vc} V at t = τ
        </text>
      </svg>

      <p className={styles.legend}>
        <span>
          <var>τ</var> = RC = {tau} s
        </span>
        <span>
          <var>Vc</var> at <var>τ</var> = {Vc} V
        </span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. The curve shows the shape of charging; only V₀ and the
        marked point are numbers from the engine.
      </figcaption>
    </figure>
  );
}
