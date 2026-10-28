import { formatValue } from "../../utils/format.ts";
import type { WireData } from "./wire.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 320;
const CX = 300;
const CY = 160;
const WIRE_HALF = 120; // px; the wire is drawn at a fixed length, its real length is labelled
const FIELD_LINES = [70, 115, 205, 250]; // y of the field lines (not through the centre)
const FIELD_LABEL_Y = 60;

/**
 * Straight wire in a uniform magnetic field, drawn from the verified answer.
 * The problem gives the angle between wire and field but not which way the
 * current or the field points, so neither has an arrowhead, and the force is a
 * label rather than an arrow.
 */
export function WireDiagram({ data }: { data: WireData }) {
  // Field lines run left to right; the wire is drawn at theta to them.
  const th = (data.thetaDeg * Math.PI) / 180;
  const dx = WIRE_HALF * Math.cos(th);
  const dy = WIRE_HALF * Math.sin(th);

  // angle mark between the field direction and the wire, at the centre
  const markR = 28;
  const markEnd = { x: CX + markR * Math.cos(th), y: CY - markR * Math.sin(th) };
  const right = Math.abs(data.thetaDeg - 90) < 1e-9;

  const B = formatValue(data.B);
  const I = formatValue(data.I);
  const L = formatValue(data.L);
  const F = formatValue(data.F);
  const angle = formatValue(data.thetaDeg);
  const summary =
    `Wire of length ${L} m carrying ${I} A, at ${angle}° to a ${B} T magnetic field. ` +
    `The force on it is ${F} N, at right angles to both the wire and the field. ` +
    `Directions are not shown because the problem does not give them.`;

  return (
    <figure className={styles.figure}>
      <svg viewBox={`0 0 ${W} ${H}`} className={styles.svg} role="img" aria-label={summary}>
        {/* field lines */}
        {FIELD_LINES.map((y) => (
          <line key={y} className={styles.fieldLine} x1={40} y1={y} x2={W - 40} y2={y} />
        ))}
        <line className={styles.fieldLine} x1={40} y1={CY} x2={W - 40} y2={CY} />
        <text className={styles.label} x={40} y={FIELD_LABEL_Y}>
          field B = {B} T
        </text>

        {/* the wire */}
        <line
          className={styles.wireThick}
          data-testid="wire"
          x1={CX - dx}
          y1={CY + dy}
          x2={CX + dx}
          y2={CY - dy}
        />
        <text className={styles.label} x={CX + dx + 12} y={CY - dy + 5}>
          wire: I = {I} A, L = {L} m
        </text>

        {/* angle between wire and field */}
        {right ? (
          <path
            className={styles.axis}
            data-testid="right-angle"
            fill="none"
            d={`M${CX + 18},${CY} L${CX + 18},${CY - 18} L${CX},${CY - 18}`}
          />
        ) : (
          <path
            className={styles.axis}
            fill="none"
            d={`M${CX + markR},${CY} A${markR},${markR} 0 0 0 ${markEnd.x},${markEnd.y}`}
          />
        )}
        <text className={styles.label} x={CX + 34} y={CY - 26}>
          {angle}°
        </text>

        <text className={styles.label} x={40} y={H - 20}>
          F = {F} N, at right angles to both the wire and the field
        </text>
      </svg>

      <p className={styles.legend}>
        <span>
          <var>F</var> = {F} N
        </span>
        <span>angle between wire and field = {angle}°</span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. The problem does not say which way the current or the
        field points, so the drawing shows no arrows. The force points out of the flat plane that
        holds the wire and the field; which side depends on those directions.
      </figcaption>
    </figure>
  );
}
