import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, positive } from "./num.ts";

export const SPRING_CARD = "MECH-ENE-SPRING";

/** Everything the diagram needs, from the engine's response. Nothing is re-solved here. */
export interface SpringData {
  m: number; // kg  (from knowns)
  k: number; // N/m (from knowns)
  x: number; // m   (from knowns, compression)
  v: number; // m/s (engine answer, speed when released)
}

/** The card's own equation: (1/2)kx^2 = (1/2)mv^2. */
export function springHolds(d: SpringData): boolean {
  return close(d.k * d.x ** 2, d.m * d.v ** 2);
}

/** Diagram data only for a verified answer that passes the check. */
export function springData(res: SolveResponse): SpringData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== SPRING_CARD || !res.answer) return null;
  const { v } = res.answer;
  const kn = res.knowns ?? {};
  if (!positive(v)) return null;
  if (!positive(kn.m) || !positive(kn.k) || !positive(kn.x)) return null;
  const d: SpringData = { m: kn.m, k: kn.k, x: kn.x, v };
  return springHolds(d) ? d : null;
}
