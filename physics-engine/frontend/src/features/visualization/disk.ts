import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, positive } from "./num.ts";

export const DISK_CARD = "MECH-ROT-TORQUE";

/** Everything the diagram needs, from the engine's response. Nothing is re-solved here. */
export interface DiskData {
  M: number; // kg  (from knowns)
  R: number; // m   (from knowns)
  tau: number; // N*m (from knowns, torque)
  t: number; // s   (from knowns)
  I: number; // kg*m^2 (engine answer)
  alpha: number; // rad/s^2 (engine answer)
  omega: number; // rad/s (engine answer, at time t)
}

/** The card's own equations: I = MR^2/2, tau = I*alpha, omega = alpha*t. */
export function diskHolds(d: DiskData): boolean {
  return (
    close(d.I, 0.5 * d.M * d.R ** 2) && close(d.tau, d.I * d.alpha) && close(d.omega, d.alpha * d.t)
  );
}

/** Diagram data only for a verified answer that passes the check. */
export function diskData(res: SolveResponse): DiskData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== DISK_CARD || !res.answer) return null;
  const { I, alpha, omega } = res.answer;
  const k = res.knowns ?? {};
  if (!positive(I) || !positive(alpha) || !positive(omega)) return null;
  if (!positive(k.M) || !positive(k.R) || !positive(k.tau) || !positive(k.t)) return null;
  const d: DiskData = { M: k.M, R: k.R, tau: k.tau, t: k.t, I, alpha, omega };
  return diskHolds(d) ? d : null;
}
