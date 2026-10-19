import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";

export const ATWOOD_CARD = "MECH-DYN-ATWOOD";

/** Everything the diagram needs, from the engine's response. Nothing is re-solved here. */
export interface AtwoodData {
  m1: number; // kg  (from knowns)
  m2: number; // kg  (from knowns)
  g: number; // m/s^2 (from knowns, injected by the engine)
  a: number; // m/s^2 (engine answer; positive means m2 goes down)
  T: number; // N    (engine answer)
}

/** Which way the masses move. "none" when the masses are equal. */
export type Motion = "m2_down" | "m1_down" | "none";

function finite(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}
function positive(v: unknown): v is number {
  return finite(v) && v > 0;
}

/**
 * Newton's second law on each mass, using the card's own sign convention
 * (formula_kb.py: T - g*m1 = a*m1 and g*m2 - T = a*m2). Checked with the engine's
 * numbers before drawing: arrows drawn from numbers that disagree would teach a
 * wrong picture, so a failed check means no diagram.
 */
export function lawsHold(d: AtwoodData, relTol = 1e-6): boolean {
  const scale = (d.m1 + d.m2) * d.g;
  const r1 = d.T - d.m1 * d.g - d.m1 * d.a;
  const r2 = d.m2 * d.g - d.T - d.m2 * d.a;
  return Math.abs(r1) <= relTol * scale && Math.abs(r2) <= relTol * scale;
}

/**
 * Returns diagram data only for a verified Atwood answer with numeric values that
 * satisfy both equations. Anything else returns null and nothing is drawn.
 */
export function atwoodData(res: SolveResponse): AtwoodData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== ATWOOD_CARD || !res.answer) return null;
  const { a, T } = res.answer;
  const k = res.knowns ?? {};
  if (!finite(a) || !positive(T)) return null;
  if (!positive(k.m1) || !positive(k.m2) || !positive(k.g)) return null;
  const d: AtwoodData = { m1: k.m1, m2: k.m2, g: k.g, a, T };
  return lawsHold(d) ? d : null;
}

/** Below this, treat the system as balanced (equal masses, a = 0). */
const STILL = 1e-9;

export function motion(d: AtwoodData): Motion {
  if (Math.abs(d.a) < STILL) return "none";
  return d.a > 0 ? "m2_down" : "m1_down";
}
