import { describe, expect, it } from "vitest";
import type { SolveResponse } from "../../api/types.ts";
import { rcData } from "./rc.ts";
import { collisionData } from "./collision.ts";
import { circularData } from "./circular.ts";
import { inclineData } from "./incline.ts";
import { circuitData } from "./circuit.ts";
import { kinematicsData } from "./kinematics.ts";
import { sphereData } from "./sphere.ts";
import { springData } from "./spring.ts";
import { orbitData } from "./orbit.ts";
import { wireData } from "./wire.ts";
import { diskData } from "./disk.ts";
import { loopData } from "./loop.ts";
import {
  CIRCUIT_RES,
  CIRCULAR_RES,
  COLLISION_RES,
  DISK_RES,
  INCLINE_RES,
  KINEMATICS_RES,
  ORBIT_RES,
  RC_RES,
  SPHERE_RES,
  SPRING_RES,
  LOOP_RES,
  WIRE_RES,
} from "./fixtures.ts";

type Guard = (res: SolveResponse) => unknown;

const GUARDS: [string, Guard, SolveResponse][] = [
  ["RC charging", rcData, RC_RES],
  ["collision", collisionData, COLLISION_RES],
  ["circular path", circularData, CIRCULAR_RES],
  ["incline", inclineData, INCLINE_RES],
  ["circuit", circuitData, CIRCUIT_RES],
  ["speed-time graph", kinematicsData, KINEMATICS_RES],
  ["charged sphere", sphereData, SPHERE_RES],
  ["spring", springData, SPRING_RES],
  ["orbit", orbitData, ORBIT_RES],
  ["wire in a field", wireData, WIRE_RES],
  ["disk", diskData, DISK_RES],
  ["loop", loopData, LOOP_RES],
];

const withAnswer = (res: SolveResponse, key: string, value: unknown) =>
  ({ ...res, answer: { ...res.answer, [key]: value } }) as SolveResponse;
const withKnown = (res: SolveResponse, key: string, value: unknown) =>
  ({ ...res, knowns: { ...res.knowns, [key]: value } }) as SolveResponse;

describe.each(GUARDS)("%s guard", (_name, guard, res) => {
  const firstAnswer = Object.keys(res.answer ?? {})[0] ?? "";
  const firstKnown = Object.keys(res.knowns ?? {})[0] ?? "";

  it("accepts the verified golden answer", () => {
    expect(guard(res)).not.toBeNull();
  });

  it("ignores extra knowns the engine injects", () => {
    expect(guard(withKnown(res, "mu_0", 1.25663706e-6))).not.toBeNull();
  });

  it.each([
    ["needs_review", { verification: "needs_review" }],
    ["an unknown state", { verification: "Verified" }],
    ["another card", { card_id: "MECH-DYN-ATWOOD" }],
    ["no card id", { card_id: undefined }],
    ["tutor mode (no answer, no knowns)", { answer: null, knowns: null }],
  ])("draws nothing for %s", (_case, change) => {
    expect(guard({ ...res, ...change } as SolveResponse)).toBeNull();
  });

  it("draws nothing for a symbolic answer", () => {
    expect(guard(withAnswer(res, firstAnswer, "x*y"))).toBeNull();
  });

  it("draws nothing for a missing known", () => {
    expect(guard(withKnown(res, firstKnown, undefined))).toBeNull();
  });

  it("draws nothing when an answer is 1% off (fails the physics check)", () => {
    const v = res.answer![firstAnswer] as number;
    expect(guard(withAnswer(res, firstAnswer, v * 1.01))).toBeNull();
  });
});

describe("card-specific checks", () => {
  it("incline: a block that would not slide (tan θ ≤ μ) is not drawn", () => {
    expect(inclineData(withKnown(INCLINE_RES, "mu", 0.7))).toBeNull();
  });

  it("incline: a frictionless slope is still drawn", () => {
    const a = 9.8 * 0.5;
    const res = {
      ...INCLINE_RES,
      knowns: { ...INCLINE_RES.knowns, mu: 0 },
      answer: { a, v: Math.sqrt(8 * a) },
    };
    expect(inclineData(res as SolveResponse)).not.toBeNull();
  });

  it("collision: a cart moving left is not drawn", () => {
    expect(collisionData(withKnown(COLLISION_RES, "v1", -4))).toBeNull();
  });

  it("circuit: branch currents that do not add up are not drawn", () => {
    expect(circuitData(withAnswer(CIRCUIT_RES, "I_branch2", 1.1))).toBeNull();
  });

  it("speed-time: a speed that goes below zero is not drawn", () => {
    const res = { ...KINEMATICS_RES, knowns: { v0: 10, a: -2, t: 8 }, answer: { v: -6, s: 16 } };
    expect(kinematicsData(res as SolveResponse)).toBeNull();
  });

  it("speed-time: slowing down to a stop is still drawn", () => {
    const res = { ...KINEMATICS_RES, knowns: { v0: 10, a: -2, t: 5 }, answer: { v: 0, s: 25 } };
    expect(kinematicsData(res as SolveResponse)).not.toBeNull();
  });

  it("charged sphere: an 'inside' point outside the sphere is not drawn", () => {
    expect(sphereData(withKnown(SPHERE_RES, "r_in", 0.2))).toBeNull();
  });

  it("orbit: an orbit radius that is not Re + h is not drawn", () => {
    expect(orbitData(withAnswer(ORBIT_RES, "r", 6371000))).toBeNull();
  });

  it("wire: a wire along the field (no force) is not drawn", () => {
    const res = {
      ...WIRE_RES,
      knowns: { ...WIRE_RES.knowns, theta_deg: 180 },
      answer: { F: 1e-16 },
    };
    expect(wireData(res as SolveResponse)).toBeNull();
  });

  it("wire: a wire at 30 degrees is drawn", () => {
    const res = { ...WIRE_RES, knowns: { ...WIRE_RES.knowns, theta_deg: 30 }, answer: { F: 0.6 } };
    expect(wireData(res as SolveResponse)).not.toBeNull();
  });

  it("disk: a hoop-style inertia (MR^2) is not drawn", () => {
    expect(diskData(withAnswer(DISK_RES, "I", 0.125))).toBeNull();
  });

  it("circular path: a negative charge is not drawn", () => {
    expect(circularData(withKnown(CIRCULAR_RES, "q", -1.602176634e-19))).toBeNull();
  });
});
