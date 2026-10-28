import type { ReactElement } from "react";
import type { SolveResponse } from "../../api/types.ts";
import { projectileData } from "./projectile.ts";
import { TrajectoryPlot } from "./TrajectoryPlot.tsx";
import { atwoodData } from "./atwood.ts";
import { AtwoodDiagram } from "./AtwoodDiagram.tsx";
import { rcData } from "./rc.ts";
import { RcCurve } from "./RcCurve.tsx";
import { collisionData } from "./collision.ts";
import { CollisionDiagram } from "./CollisionDiagram.tsx";
import { circularData } from "./circular.ts";
import { CircularPathDiagram } from "./CircularPathDiagram.tsx";
import { inclineData } from "./incline.ts";
import { InclineDiagram } from "./InclineDiagram.tsx";
import { circuitData } from "./circuit.ts";
import { CircuitDiagram } from "./CircuitDiagram.tsx";
import { kinematicsData } from "./kinematics.ts";
import { SpeedTimeGraph } from "./SpeedTimeGraph.tsx";
import { sphereData } from "./sphere.ts";
import { SphereFieldGraph } from "./SphereFieldGraph.tsx";
import { springData } from "./spring.ts";
import { SpringDiagram } from "./SpringDiagram.tsx";
import { orbitData } from "./orbit.ts";
import { OrbitDiagram } from "./OrbitDiagram.tsx";
import { wireData } from "./wire.ts";
import { WireDiagram } from "./WireDiagram.tsx";
import { diskData } from "./disk.ts";
import { DiskDiagram } from "./DiskDiagram.tsx";
import { loopData } from "./loop.ts";
import { LoopDiagram } from "./LoopDiagram.tsx";

/**
 * One entry per diagram. Each guard returns null unless the response is a
 * verified answer from its own card whose numbers pass its check, so at most
 * one entry can match. To add a diagram, add a line here.
 */
const DIAGRAMS: ((res: SolveResponse) => ReactElement | null)[] = [
  (res) => {
    const d = projectileData(res);
    return d && <TrajectoryPlot data={d} />;
  },
  (res) => {
    const d = atwoodData(res);
    return d && <AtwoodDiagram data={d} />;
  },
  (res) => {
    const d = rcData(res);
    return d && <RcCurve data={d} />;
  },
  (res) => {
    const d = collisionData(res);
    return d && <CollisionDiagram data={d} />;
  },
  (res) => {
    const d = circularData(res);
    return d && <CircularPathDiagram data={d} />;
  },
  (res) => {
    const d = inclineData(res);
    return d && <InclineDiagram data={d} />;
  },
  (res) => {
    const d = circuitData(res);
    return d && <CircuitDiagram data={d} />;
  },
  (res) => {
    const d = kinematicsData(res);
    return d && <SpeedTimeGraph data={d} />;
  },
  (res) => {
    const d = sphereData(res);
    return d && <SphereFieldGraph data={d} />;
  },
  (res) => {
    const d = springData(res);
    return d && <SpringDiagram data={d} />;
  },
  (res) => {
    const d = orbitData(res);
    return d && <OrbitDiagram data={d} />;
  },
  (res) => {
    const d = wireData(res);
    return d && <WireDiagram data={d} />;
  },
  (res) => {
    const d = diskData(res);
    return d && <DiskDiagram data={d} />;
  },
  (res) => {
    const d = loopData(res);
    return d && <LoopDiagram data={d} />;
  },
];

/** Picks a diagram for the response, or renders nothing. */
export function Visualization({ data }: { data: SolveResponse }) {
  for (const pick of DIAGRAMS) {
    const el = pick(data);
    if (el) return el;
  }
  return null;
}