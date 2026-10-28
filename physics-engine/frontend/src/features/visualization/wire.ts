import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, positive } from "./num.ts";

export const WIRE_CARD = "EM-MAG-FORCE-WIRE";

/** Everything the diagram needs, from the engine's response. Nothing is re-solved here. */
export interface WireData {
  B: number; // T  (from knowns)
  I: number; // A  (from knowns)
  L: number; // m  (from knowns)
  thetaDeg: number; // degrees between wire and field (from knowns)
  F: number; // N  (engine answer)
}

/** The card's own equation: F = B*I*L*sin(theta). */
export function wireHolds(d: WireData): boolean {
  if (d.thetaDeg <= 0 || d.thetaDeg >= 180) return false;
  return close(d.F, d.B * d.I * d.L * Math.sin((d.thetaDeg * Math.PI) / 180));
}

/** Diagram data only for a verified answer that passes the check. */
export function wireData(res: SolveResponse): WireData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== WIRE_CARD || !res.answer) return null;
  const { F } = res.answer;
  const k = res.knowns ?? {};
  if (!positive(F)) return null;
  if (!positive(k.B) || !positive(k.I) || !positive(k.L) || !positive(k.theta_deg)) return null;
  const d: WireData = { B: k.B, I: k.I, L: k.L, thetaDeg: k.theta_deg, F };
  return wireHolds(d) ? d : null;
}