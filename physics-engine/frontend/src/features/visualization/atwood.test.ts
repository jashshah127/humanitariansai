import { describe, expect, it } from "vitest";
import type { SolveResponse } from "../../api/types.ts";
import { atwoodData, lawsHold, motion } from "./atwood.ts";

// Real engine output for the golden-set Atwood problem (4 kg and 6 kg).
const base: SolveResponse = {
  verification: "verified",
  badge: "Verified - solved symbolically",
  needs_llm_completion: false,
  explanation: "",
  route: "deterministic_script",
  card_id: "MECH-DYN-ATWOOD",
  knowns: { m1: 4, m2: 6, g: 9.8 },
  answer: { a: 1.9600000000000002, T: 47.040000000000006 },
};

describe("atwoodData guard", () => {
  it("accepts a verified Atwood answer", () => {
    expect(atwoodData(base)).toEqual({
      m1: 4,
      m2: 6,
      g: 9.8,
      a: 1.9600000000000002,
      T: 47.040000000000006,
    });
  });

  it.each([
    ["needs_review", { verification: "needs_review" }],
    ["an unknown state", { verification: "Verified" }],
    ["another card", { card_id: "MECH-KIN-PROJ" }],
    ["tutor mode (no answer, no knowns)", { answer: null, knowns: null }],
    ["a symbolic answer", { answer: { a: "g*(m2 - m1)/(m1 + m2)", T: "2*g*m1*m2/(m1 + m2)" } }],
    ["a symbolic mass", { knowns: { m1: "m1", m2: 6, g: 9.8 } }],
    ["a missing g", { knowns: { m1: 4, m2: 6 } }],
    ["zero tension", { answer: { a: 1.96, T: 0 } }],
  ])("draws nothing for %s", (_name, change) => {
    expect(atwoodData({ ...base, ...change } as SolveResponse)).toBeNull();
  });

  // The cross-check: numbers that break Newton's second law are not drawn.
  it.each([
    ["a wrong tension", { a: 1.96, T: 50 }],
    ["a flipped sign on a", { a: -1.96, T: 47.04 }],
  ])("draws nothing for %s", (_name, answer) => {
    expect(atwoodData({ ...base, answer })).toBeNull();
  });
});

describe("lawsHold", () => {
  it("holds for the textbook check (OpenStax: 2 kg and 4 kg)", () => {
    // Published: a = 3.27 m/s², T = 26.1 N. Exact: a = g/3, T = 8g/3.
    expect(lawsHold({ m1: 2, m2: 4, g: 9.8, a: 9.8 / 3, T: (8 * 9.8) / 3 })).toBe(true);
  });
});

describe("motion", () => {
  it("follows the sign of a: positive means m2 goes down", () => {
    expect(motion({ m1: 4, m2: 6, g: 9.8, a: 1.96, T: 47.04 })).toBe("m2_down");
    expect(motion({ m1: 6, m2: 4, g: 9.8, a: -1.96, T: 47.04 })).toBe("m1_down");
    expect(motion({ m1: 5, m2: 5, g: 9.8, a: 0, T: 49 })).toBe("none");
  });
});
