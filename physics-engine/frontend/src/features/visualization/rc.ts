import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, positive } from "./num.ts";

export const RC_CARD = "EM-CIRC-RC-CHARGE-1TAU";

/** Everything the curve needs, from the engine's response. Nothing is re-solved here. */
export interface RcData {
  R: number; // ohm (from knowns)
  C: number; // F   (from knowns)
  V0: number; // V  (from knowns)
  tau: number; // s (engine answer)
  Vc: number; // V  (engine answer, capacitor voltage at t = tau)
}

/** The card's own equations: tau = R*C and Vc = V0*(1 - 1/e). */
export function rcHolds(d: RcData): boolean {
  return close(d.tau, d.R * d.C) && close(d.Vc, d.V0 * (1 - Math.exp(-1)));
}

/** Diagram data only for a verified RC answer whose numbers pass the check. */
export function rcData(res: SolveResponse): RcData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== RC_CARD || !res.answer) return null;
  const { tau, Vc } = res.answer;
  const k = res.knowns ?? {};
  if (!positive(tau) || !positive(Vc)) return null;
  if (!positive(k.R) || !positive(k.C) || !positive(k.V0)) return null;
  const d: RcData = { R: k.R, C: k.C, V0: k.V0, tau, Vc };
  return rcHolds(d) ? d : null;
}

/** Capacitor voltage at time t. Used only for the curve's shape, never printed. */
export function chargeAt(t: number, d: RcData): number {
  return d.V0 * (1 - Math.exp(-t / d.tau));
}
