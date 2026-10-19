import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";

export const PROJECTILE_CARD = "MECH-KIN-PROJ";

/** Everything the plot needs, taken from the engine's response. Nothing is re-solved here. */
export interface ProjectileData {
  range: number; // m   (engine's range_)
  height: number; // m  (engine's h_max)
  flightTime: number; // s (engine's t_flight)
  v0: number | null; // m/s, label only
  thetaDeg: number | null; // degrees, label only
}

function positive(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v) && v > 0;
}

/**
 * Returns plot data only for a verified projectile answer with three positive
 * numbers. Anything else (symbolic answer, other card, needs_review, tutor
 * mode) returns null, and no plot is drawn. A wrong picture is worse than none.
 */
export function projectileData(res: SolveResponse): ProjectileData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== PROJECTILE_CARD || !res.answer) return null;
  const { range_, h_max, t_flight } = res.answer;
  if (!positive(range_) || !positive(h_max) || !positive(t_flight)) return null;
  const k = res.knowns ?? {};
  return {
    range: range_,
    height: h_max,
    flightTime: t_flight,
    v0: positive(k.v0) ? k.v0 : null,
    thetaDeg: positive(k.theta_deg) ? k.theta_deg : null,
  };
}

/**
 * Position at time t, built only from the three solved values.
 * Horizontal speed is constant, so x grows linearly with time. Height is the
 * parabola through (0,0), (R/2,H) and (R,0). For equal launch and landing
 * height this is exactly y = v0·sinθ·t − g·t²/2, so the picture matches the
 * numbers on screen by construction.
 */
export function positionAt(t: number, d: ProjectileData): { x: number; y: number } {
  const u = Math.min(Math.max(t / d.flightTime, 0), 1);
  return { x: d.range * u, y: 4 * d.height * u * (1 - u) };
}
