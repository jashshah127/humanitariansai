import type { SolveResponse } from "../../api/types.ts";
import { normalizeVerification } from "../../design/components/verification.ts";
import { close, positive } from "./num.ts";

export const CIRCUIT_CARD = "EM-CIRC-SERIES-PARALLEL";

/** Everything the diagram needs, from the engine's response. Nothing is re-solved here. */
export interface CircuitData {
  R1: number; // ohm (from knowns, series pair)
  R2: number; // ohm (from knowns, series pair)
  R3: number; // ohm (from knowns, the parallel resistor)
  V: number; // V   (from knowns)
  Rs: number; // ohm (engine R_series)
  Req: number; // ohm (engine R_eq)
  It: number; // A   (engine I_total)
  I1: number; // A   (engine I_branch1, through R1 and R2)
  I2: number; // A   (engine I_branch2, through R3)
}

/** The card's own equations, plus the card's own check that branch currents add up. */
export function circuitHolds(d: CircuitData): boolean {
  return (
    close(d.Rs, d.R1 + d.R2) &&
    close(d.Req, (d.Rs * d.R3) / (d.Rs + d.R3)) &&
    close(d.It, d.V / d.Req) &&
    close(d.I1, d.V / d.Rs) &&
    close(d.I2, d.V / d.R3) &&
    close(d.I1 + d.I2, d.It)
  );
}

/** Diagram data only for a verified circuit answer that passes the check. */
export function circuitData(res: SolveResponse): CircuitData | null {
  if (normalizeVerification(res.verification) !== "verified") return null;
  if (res.card_id !== CIRCUIT_CARD || !res.answer) return null;
  const { R_series, R_eq, I_total, I_branch1, I_branch2 } = res.answer;
  const k = res.knowns ?? {};
  if (!positive(R_series) || !positive(R_eq) || !positive(I_total)) return null;
  if (!positive(I_branch1) || !positive(I_branch2)) return null;
  if (!positive(k.R1) || !positive(k.R2) || !positive(k.R3) || !positive(k.V)) return null;
  const d: CircuitData = {
    R1: k.R1,
    R2: k.R2,
    R3: k.R3,
    V: k.V,
    Rs: R_series,
    Req: R_eq,
    It: I_total,
    I1: I_branch1,
    I2: I_branch2,
  };
  return circuitHolds(d) ? d : null;
}
