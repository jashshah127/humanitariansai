import type { SolveResponse } from "../../api/types.ts";
import { projectileData } from "./projectile.ts";
import { TrajectoryPlot } from "./TrajectoryPlot.tsx";
import { atwoodData } from "./atwood.ts";
import { AtwoodDiagram } from "./AtwoodDiagram.tsx";

/**
 * Picks a diagram for the response, or renders nothing.
 * Each diagram has its own guard; add new problem types here (Atwood is next).
 */
export function Visualization({ data }: { data: SolveResponse }) {
  const proj = projectileData(data);
  if (proj) return <TrajectoryPlot data={proj} />;
  const atw = atwoodData(data);
  if (atw) return <AtwoodDiagram data={atw} />;
  return null;
}
