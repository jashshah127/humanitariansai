import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, positive } from "./num.ts";

export const SPHERE_CARD = "EM-ELEC-GAUSS-SPHERE";

/** Everything the graph needs, from the engine's response. Nothing is re-solved here. */
export interface SphereData {
  ke: number; // N m^2/C^2 (from knowns, injected by the engine)
  Q: number; // C  (from knowns, total charge)
  R: number; // m  (from knowns, sphere radius)
  rIn: number; // m (from knowns, point inside)
  rOut: number; // m (from knowns, point outside)
  Ein: number; // N/C (engine answer)
  Eout: number; // N/C (engine answer)
}

/** The card's own equations: E = keQr/R^3 inside, E = keQ/r^2 outside. */
export function sphereHolds(d: SphereData): boolean {
  if (d.rIn > d.R || d.rOut < d.R) return false;
  return close(d.Ein, (d.ke * d.Q * d.rIn) / d.R ** 3) && close(d.Eout, (d.ke * d.Q) / d.rOut ** 2);
}

/** Diagram data only for a verified answer that passes the check. */
export function sphereData(res: SolveResponse): SphereData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== SPHERE_CARD || !res.answer) return null;
  const { E_in, E_out } = res.answer;
  const k = res.knowns ?? {};
  if (!positive(E_in) || !positive(E_out)) return null;
  if (!positive(k.k_e) || !positive(k.Q) || !positive(k.R)) return null;
  if (!positive(k.r_in) || !positive(k.r_out)) return null;
  const d: SphereData = {
    ke: k.k_e,
    Q: k.Q,
    R: k.R,
    rIn: k.r_in,
    rOut: k.r_out,
    Ein: E_in,
    Eout: E_out,
  };
  return sphereHolds(d) ? d : null;
}

/** Field size at distance r, used only for the curve's shape. Never printed. */
export function fieldAt(r: number, d: SphereData): number {
  return r <= d.R ? (d.ke * d.Q * r) / d.R ** 3 : (d.ke * d.Q) / r ** 2;
}
