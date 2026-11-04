import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, finite, positive } from "./num.ts";

export const COLLISION_CARD = "MECH-MOM-INELASTIC";

/** Everything the diagram needs, from the engine's response. Nothing is re-solved here. */
export interface CollisionData {
  m1: number; // kg  (from knowns, the moving cart)
  v1: number; // m/s (from knowns)
  m2: number; // kg  (from knowns, starts at rest)
  vf: number; // m/s (engine answer, both carts together)
  KEi: number; // J  (engine answer)
  KEf: number; // J  (engine answer)
  dKE: number; // J  (engine answer, energy lost)
}

/** The card's own equations: momentum kept, KE before/after, and the loss. */
export function collisionHolds(d: CollisionData): boolean {
  return (
    close(d.m1 * d.v1, (d.m1 + d.m2) * d.vf) &&
    close(d.KEi, 0.5 * d.m1 * d.v1 ** 2) &&
    close(d.KEf, 0.5 * (d.m1 + d.m2) * d.vf ** 2) &&
    close(d.dKE, d.KEi - d.KEf)
  );
}

/**
 * Diagram data only for a verified collision answer that passes the check.
 * v1 must be positive (cart moving right); anything else is not drawn.
 */
export function collisionData(res: SolveResponse): CollisionData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== COLLISION_CARD || !res.answer) return null;
  const { vf, KEi, KEf, dKE } = res.answer;
  const k = res.knowns ?? {};
  if (!positive(vf) || !positive(KEi) || !finite(KEf) || KEf < 0 || !positive(dKE)) return null;
  if (!positive(k.m1) || !positive(k.v1) || !positive(k.m2)) return null;
  const d: CollisionData = { m1: k.m1, v1: k.v1, m2: k.m2, vf, KEi, KEf, dKE };
  return collisionHolds(d) ? d : null;
}
