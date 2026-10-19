import { useEffect, useId, useRef, useState } from "react";
import { formatValue } from "../../utils/format.ts";
import { positionAt, type ProjectileData } from "./projectile.ts";
import styles from "./visualization.module.css";

const W = 600; // viewBox width
const PAD = 40;
const MIN_H = 140;
const STEPS = 200; // slider resolution
const PLAY_MS = 3000; // playback length; NOT real time, shown in the caption

function prefersReducedMotion(): boolean {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}

export function TrajectoryPlot({ data }: { data: ProjectileData }) {
  const [step, setStep] = useState(STEPS);
  const [playing, setPlaying] = useState(false);
  const raf = useRef<number | null>(null);
  const sliderId = useId();

  // Same scale on both axes, so the launch angle looks like the real angle.
  const plotW = W - 2 * PAD;
  const scale = plotW / data.range;
  const H = Math.max(MIN_H, data.height * scale + 2 * PAD);
  const sx = (x: number) => PAD + x * scale;
  const sy = (y: number) => H - PAD - y * scale;

  const path = Array.from({ length: 61 }, (_, i) => {
    const p = positionAt((i / 60) * data.flightTime, data);
    return `${i === 0 ? "M" : "L"}${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`;
  }).join(" ");

  const t = (step / STEPS) * data.flightTime;
  const now = positionAt(t, data);

  useEffect(() => {
    if (!playing) return;
    const start = performance.now();
    const tick = (ms: number) => {
      const s = Math.min(STEPS, Math.round(((ms - start) / PLAY_MS) * STEPS));
      setStep(s);
      if (s < STEPS) raf.current = requestAnimationFrame(tick);
      else setPlaying(false);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current !== null) cancelAnimationFrame(raf.current);
    };
  }, [playing]);

  const summary =
    `Projectile path: range ${formatValue(data.range)} m, ` +
    `maximum height ${formatValue(data.height)} m, flight time ${formatValue(data.flightTime)} s.`;

  return (
    <figure className={styles.figure}>
      <svg viewBox={`0 0 ${W} ${H}`} className={styles.svg} role="img" aria-label={summary}>
        <line className={styles.ground} x1={PAD} y1={sy(0)} x2={W - PAD} y2={sy(0)} />
        <path className={styles.path} d={path} />
        {/* apex */}
        <line
          className={styles.guide}
          x1={sx(data.range / 2)}
          y1={sy(0)}
          x2={sx(data.range / 2)}
          y2={sy(data.height)}
        />
        <text className={styles.label} x={sx(data.range / 2) + 6} y={sy(data.height / 2)}>
          h_max = {formatValue(data.height)} m
        </text>
        {/* range */}
        <text className={styles.label} x={sx(data.range / 2)} y={sy(0) + 24} textAnchor="middle">
          range = {formatValue(data.range)} m
        </text>
        {data.thetaDeg !== null && (
          <text className={styles.label} x={sx(0) + 8} y={sy(0) - 8}>
            {formatValue(data.thetaDeg)}°
          </text>
        )}
        <circle className={styles.ball} cx={sx(now.x)} cy={sy(now.y)} r={6} />
      </svg>

      <div className={styles.controls}>
        {!prefersReducedMotion() && (
          <button
            type="button"
            className={styles.play}
            onClick={() => {
              setStep(0);
              setPlaying(true);
            }}
            disabled={playing}
          >
            {playing ? "Playing…" : "Play"}
          </button>
        )}
        <label htmlFor={sliderId} className={styles.sliderLabel}>
          Time
        </label>
        <input
          id={sliderId}
          type="range"
          min={0}
          max={STEPS}
          value={step}
          onChange={(e) => {
            setPlaying(false);
            setStep(Number(e.target.value));
          }}
          aria-valuetext={`${formatValue(t)} seconds`}
        />
        <output className={styles.readout} aria-live="off">
          t = {formatValue(t)} s · x = {formatValue(now.x)} m · y = {formatValue(now.y)} m
        </output>
      </div>

      <figcaption className={styles.caption}>
        Drawn from the verified answer above, assuming equal launch and landing height
        {data.v0 !== null && <> and launch speed {formatValue(data.v0)} m/s</>}. Playback is sped up
        or slowed to 3 seconds.
      </figcaption>
    </figure>
  );
}
