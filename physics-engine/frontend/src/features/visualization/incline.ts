import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, finite, positive } from "./num.ts";

export const INCLINE_CARD = "MECH-DYN-INCLINE";

/** Everything the diagram needs, from the engine's response. Nothing is re-solved here. */
export interface InclineData {
  thetaDeg: number; // degrees (from knowns)
  mu: number; // friction coefficient (from knowns)
  g: number; // m/s^2 (from knowns, injected by the engine)
  d: number; // m, distance slid (from knowns)
  a: number; // m/s^2 (engine answer, down the slope)
  v: number; // m/s (engine answer, speed after d)
}

/**
 * The card's own equations, plus its applicability rule: the block only slides
 * when tan(theta) > mu. A "sliding" picture for a block that stays put would be wrong.
 */
export function inclineHolds(d: InclineData): boolean {
  if (d.thetaDeg <= 0 || d.thetaDeg >= 90) return false;
  const th = (d.thetaDeg * Math.PI) / 180;
  if (Math.tan(th) <= d.mu) return false;
  return (
    close(d.a, d.g * (Math.sin(th) - d.mu * Math.cos(th))) && close(d.v, Math.sqrt(2 * d.a * d.d))
  );
}

/** Diagram data only for a verified incline answer that passes the check. */
export function inclineData(res: SolveResponse): InclineData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== INCLINE_CARD || !res.answer) return null;
  const { a, v } = res.answer;
  const k = res.knowns ?? {};
  if (!positive(a) || !positive(v)) return null;
  if (!positive(k.theta_deg) || !finite(k.mu) || k.mu < 0) return null;
  if (!positive(k.g) || !positive(k.d)) return null;
  const d: InclineData = { thetaDeg: k.theta_deg, mu: k.mu, g: k.g, d: k.d, a, v };
  return inclineHolds(d) ? d : null;
}
