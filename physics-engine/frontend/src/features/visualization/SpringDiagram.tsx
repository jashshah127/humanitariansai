import { useId } from "react";
import { formatValue } from "../../utils/format.ts";
import type { SpringData } from "./spring.ts";
import styles from "./visualization.module.css";

const W = 600;
const H = 320;
const WALL_X = 40;
const BLOCK = 56;
const NATURAL = 230; // px, spring at its natural length
const SQUASHED = 130; // px, compressed (not to scale)
const COMPRESSED_Y = 130; // ground line, before release
const RELEASED_Y = 270; // ground line, after release
const V_ARROW = 120;

/** Horizontal zigzag spring from x1 to x2 at height y. */
function coil(x1: number, x2: number, y: number): string {
  const turns = 10;
  const lead = 12;
  const step = (x2 - x1 - 2 * lead) / turns;
  const pts = [`M${x1},${y}`, `L${x1 + lead},${y}`];
  for (let i = 0; i < turns; i++) {
    pts.push(`L${x1 + lead + step * (i + 0.5)},${y + (i % 2 === 0 ? -12 : 12)}`);
  }
  pts.push(`L${x2 - lead},${y}`, `L${x2},${y}`);
  return pts.join(" ");
}

/**
 * Spring launcher, drawn from the verified answer: compressed by x, then released
 * with speed v on a frictionless surface. Printed numbers are engine values only.
 * Lengths are not to scale.
 */
export function SpringDiagram({ data }: { data: SpringData }) {
  const uid = useId().replace(/:/g, "");
  const head = `${uid}-v`;
  const dim = `${uid}-dim`;

  const m = formatValue(data.m);
  const k = formatValue(data.k);
  const x = formatValue(data.x);
  const v = formatValue(data.v);
  const summary =
    `Spring: a ${m} kg block pushes a spring with k = ${k} N/m in by ${x} m on a frictionless ` +
    `surface. When released, the spring's stored energy becomes the block's kinetic energy, ` +
    `and it moves off at ${v} m/s.`;

  const row = (ground: number, springLen: number, title: string, moving: boolean) => {
    const midY = ground - BLOCK / 2;
    const blockX = WALL_X + springLen;
    return (
      <g>
        <text className={styles.rowTitle} x={WALL_X} y={ground - BLOCK - 22}>
          {title}
        </text>
        <line className={styles.ground} x1={16} y1={ground} x2={W - 16} y2={ground} />
        <line
          className={styles.wall}
          x1={WALL_X}
          y1={ground}
          x2={WALL_X}
          y2={ground - BLOCK - 10}
        />
        <path className={styles.wire} d={coil(WALL_X, blockX, midY)} />
        <rect
          className={styles.box}
          x={blockX}
          y={ground - BLOCK}
          width={BLOCK}
          height={BLOCK}
          rx={4}
        />
        <text className={styles.label} x={blockX + BLOCK / 2} y={midY + 5} textAnchor="middle">
          {m} kg
        </text>
        {moving && (
          <>
            <line
              className={styles.force}
              data-testid="v-arrow"
              x1={blockX + BLOCK + 10}
              y1={midY}
              x2={blockX + BLOCK + 10 + V_ARROW}
              y2={midY}
              markerEnd={`url(#${head})`}
            />
            <text
              className={styles.label}
              x={blockX + BLOCK + 10 + V_ARROW / 2}
              y={midY - 12}
              textAnchor="middle"
            >
              v = {v} m/s
            </text>
          </>
        )}
      </g>
    );
  };

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
          <marker
            id={dim}
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path className={styles.plainHead} d="M0,0 L10,5 L0,10 z" />
          </marker>
        </defs>

        {row(COMPRESSED_Y, SQUASHED, "Pushed in", false)}
        {/* how far it is pushed in: from the block's face to where the spring would rest */}
        <line
          className={styles.guide}
          x1={WALL_X + NATURAL}
          y1={COMPRESSED_Y - BLOCK - 6}
          x2={WALL_X + NATURAL}
          y2={COMPRESSED_Y}
        />
        <line
          className={styles.axis}
          data-testid="compression"
          x1={WALL_X + SQUASHED + BLOCK + 4}
          y1={COMPRESSED_Y - BLOCK - 2}
          x2={WALL_X + NATURAL - 2}
          y2={COMPRESSED_Y - BLOCK - 2}
          markerStart={`url(#${dim})`}
          markerEnd={`url(#${dim})`}
        />
        <text className={styles.label} x={WALL_X + NATURAL + 8} y={COMPRESSED_Y - BLOCK + 2}>
          x = {x} m
        </text>
        <text className={styles.label} x={W - 24} y={COMPRESSED_Y - BLOCK - 22} textAnchor="end">
          k = {k} N/m
        </text>

        {row(RELEASED_Y, NATURAL, "Released (frictionless surface)", true)}
      </svg>

      <p className={styles.legend}>
        <span>Spring energy becomes kinetic energy</span>
        <span>
          <var>v</var> = {v} m/s
        </span>
      </p>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above. Lengths are not to scale. The dashed line marks where
        the spring&apos;s end sits when it is not pushed in.
      </figcaption>
    </figure>
  );
}
