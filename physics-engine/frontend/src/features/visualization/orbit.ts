import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, positive } from "./num.ts";

export const ORBIT_CARD = "MECH-GRAV-ORBIT";

/** Everything the diagram needs, from the engine's response. Nothing is re-solved here. */
export interface OrbitData {
  G: number; // (from knowns, injected by the engine)
  M: number; // kg (from knowns, the central body)
  h: number; // m  (from knowns, altitude above the surface)
  Re: number; // m (from knowns, radius of the central body)
  r: number; // m  (engine answer, orbit radius from the centre)
  v: number; // m/s (engine answer)
  T: number; // s  (engine answer, one orbit)
}

/** The card's own equations: r = Re + h, v = sqrt(GM/r), T = 2*pi*r/v. */
export function orbitHolds(d: OrbitData): boolean {
  return (
    close(d.r, d.Re + d.h) &&
    close(d.v, Math.sqrt((d.G * d.M) / d.r)) &&
    close(d.T, (2 * Math.PI * d.r) / d.v)
  );
}

/** Diagram data only for a verified answer that passes the check. */
export function orbitData(res: SolveResponse): OrbitData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== ORBIT_CARD || !res.answer) return null;
  const { r, v, T } = res.answer;
  const k = res.knowns ?? {};
  if (!positive(r) || !positive(v) || !positive(T)) return null;
  if (!positive(k.G) || !positive(k.M) || !positive(k.h) || !positive(k.Re)) return null;
  const d: OrbitData = { G: k.G, M: k.M, h: k.h, Re: k.Re, r, v, T };
  return orbitHolds(d) ? d : null;
}