import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, positive } from "./num.ts";

export const CIRCULAR_CARD = "EM-MAG-LORENTZ-CIRCULAR";

/** Everything the diagram needs, from the engine's response. Nothing is re-solved here. */
export interface CircularData {
  q: number; // C   (from knowns)
  m: number; // kg  (from knowns)
  v: number; // m/s (from knowns)
  B: number; // T   (from knowns)
  r: number; // m   (engine answer)
  T: number; // s   (engine answer, time for one loop)
}

/** The card's own equations: r = m*v/(q*B), and one loop takes T = 2*pi*r/v. */
export function circularHolds(d: CircularData): boolean {
  return close(d.r, (d.m * d.v) / (d.q * d.B)) && close(d.T, (2 * Math.PI * d.r) / d.v);
}

/** Diagram data only for a verified answer that passes the check. */
export function circularData(res: SolveResponse): CircularData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== CIRCULAR_CARD || !res.answer) return null;
  const { r, T } = res.answer;
  const k = res.knowns ?? {};
  if (!positive(r) || !positive(T)) return null;
  if (!positive(k.q) || !positive(k.m) || !positive(k.v) || !positive(k.B)) return null;
  const d: CircularData = { q: k.q, m: k.m, v: k.v, B: k.B, r, T };
  return circularHolds(d) ? d : null;
}
