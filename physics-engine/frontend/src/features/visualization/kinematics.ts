import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, finite, positive } from "./num.ts";

export const KINEMATICS_CARD = "MECH-KIN-1D";

/** Everything the graph needs, from the engine's response. Nothing is re-solved here. */
export interface KinematicsData {
  v0: number; // m/s   (from knowns)
  a: number; // m/s^2  (from knowns)
  t: number; // s      (from knowns)
  v: number; // m/s    (engine answer, speed at time t)
  s: number; // m      (engine answer, distance in that time)
}

/** The card's own equations: v = v0 + a*t and s = v0*t + a*t^2/2. */
export function kinematicsHolds(d: KinematicsData): boolean {
  return close(d.v, d.v0 + d.a * d.t) && close(d.s, d.v0 * d.t + (d.a * d.t ** 2) / 2);
}

/**
 * Diagram data only for a verified answer that passes the check. Speeds must stay
 * zero or above for the whole time: a graph that dips below zero means the object
 * turned around, and "distance travelled" would no longer be the area shown.
 */
export function kinematicsData(res: SolveResponse): KinematicsData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== KINEMATICS_CARD || !res.answer) return null;
  const { v, s } = res.answer;
  const k = res.knowns ?? {};
  if (!finite(v) || v < 0 || !positive(s)) return null;
  if (!finite(k.v0) || k.v0 < 0 || !finite(k.a) || !positive(k.t)) return null;
  if (Math.max(k.v0, v) <= 0) return null;
  const d: KinematicsData = { v0: k.v0, a: k.a, t: k.t, v, s };
  return kinematicsHolds(d) ? d : null;
}
