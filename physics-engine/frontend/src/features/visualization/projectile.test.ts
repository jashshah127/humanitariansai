import { describe, expect, it } from "vitest";
import type { SolveResponse } from "../../api/types.ts";
import { positionAt, projectileData } from "./projectile.ts";

// The real engine response for the golden-set projectile (v0 = 25 m/s, 40°).
const base: SolveResponse = {
  verification: "verified",
  badge: "Verified - solved symbolically",
  needs_llm_completion: false,
  explanation: "",
  route: "deterministic_script",
  card_id: "MECH-KIN-PROJ",
  knowns: { v0: 25, theta_deg: 40, g: 9.8 },
  answer: { t_flight: 3.27952862084969, h_max: 13.175252269341033, range_: 62.80661690128878 },
};

describe("projectileData guard", () => {
  it("accepts a verified projectile answer", () => {
    expect(projectileData(base)).toMatchObject({ v0: 25, thetaDeg: 40 });
  });

  it.each([
    ["needs_review", { ...base, verification: "needs_review" }],
    ["unknown state", { ...base, verification: "verfied" }],
    ["another card", { ...base, card_id: "MECH-DYN-ATWOOD" }],
    ["no card id", { ...base, card_id: undefined }],
    ["tutor mode (no answer)", { ...base, answer: null }],
    ["symbolic answer", { ...base, answer: { ...base.answer, range_: "v0**2*sin(2*theta)/g" } }],
    ["zero range", { ...base, answer: { ...base.answer, range_: 0 } }],
    ["NaN height", { ...base, answer: { ...base.answer, h_max: Number.NaN } }],
  ])("draws nothing for %s", (_name, res) => {
    expect(projectileData(res as SolveResponse)).toBeNull();
  });
});

describe("positionAt", () => {
  const d = projectileData(base)!;

  it("starts at the origin, peaks at h_max halfway, lands at the range", () => {
    expect(positionAt(0, d)).toEqual({ x: 0, y: 0 });
    const apex = positionAt(d.flightTime / 2, d);
    expect(apex.x).toBeCloseTo(d.range / 2, 9);
    expect(apex.y).toBeCloseTo(d.height, 9);
    const end = positionAt(d.flightTime, d);
    expect(end.x).toBeCloseTo(d.range, 9);
    expect(end.y).toBeCloseTo(0, 9);
  });

  // Independent check against the physics, not the parabola formula:
  // y(t) = v0·sinθ·t − g·t²/2 at t = 1 s.
  it("matches the kinematics equation at an arbitrary time", () => {
    const t = 1;
    const th = (40 * Math.PI) / 180;
    expect(positionAt(t, d).y).toBeCloseTo(25 * Math.sin(th) * t - (9.8 * t * t) / 2, 6);
    expect(positionAt(t, d).x).toBeCloseTo(25 * Math.cos(th) * t, 6);
  });

  it("clamps times outside the flight", () => {
    expect(positionAt(-1, d)).toEqual({ x: 0, y: 0 });
    expect(positionAt(99, d).x).toBeCloseTo(d.range, 9);
  });
});
