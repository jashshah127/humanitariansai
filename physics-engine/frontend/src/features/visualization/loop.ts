import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, positive } from "./num.ts";

export const LOOP_CARD = "EM-IND-FARADAY";

/** Everything the diagram needs, from the engine's response. Nothing is re-solved here. */
export interface LoopData {
  r: number; // m   (from knowns, loop radius)
  dBdt: number; // T/s (from knowns)
  A: number; // m^2 (engine answer)
  EMF: number; // V (engine answer)
}

/** The card's own equations: A = pi*r^2, EMF = A*dB/dt. */
export function loopHolds(d: LoopData): boolean {
  return close(d.A, Math.PI * d.r ** 2) && close(d.EMF, d.A * d.dBdt);
}

/** Diagram data only for a verified answer that passes the check. */
export function loopData(res: SolveResponse): LoopData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== LOOP_CARD || !res.answer) return null;
  const { A, EMF } = res.answer;
  const k = res.knowns ?? {};
  if (!positive(A) || !positive(EMF)) return null;
  if (!positive(k.r) || !positive(k.dBdt)) return null;
  const d: LoopData = { r: k.r, dBdt: k.dBdt, A, EMF };
  return loopHolds(d) ? d : null;
}
