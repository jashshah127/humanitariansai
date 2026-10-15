import { describe, expect, it } from "vitest";
import { canSeeReference, normalizeAssessment, parseAnswer } from "./answer.ts";

describe("parseAnswer", () => {
  it.each<[string, number]>([
    ["1.96", 1.96],
    [" -1.96 ", -1.96],
    ["+3", 3],
    [".5", 0.5],
    ["4.704e1", 47.04],
    ["\u22122", -2],
  ])("reads %j as %d", (raw, value) => {
    expect(parseAnswer(raw)).toEqual({ ok: true, value });
  });

  it.each<[string, string]>([
    ["", "Enter a number."],
    ["1,5", "Use a dot for decimals, and no commas."],
    ["abc", "Enter a number, like 9.8 or -1.5e3."],
    ["1e999", "That number is too large."],
  ])("rejects %j", (raw, error) => {
    expect(parseAnswer(raw)).toEqual({ ok: false, error });
  });

  it("tells the student not to type the unit", () => {
    expect(parseAnswer("1.96 m/s^2", "m/s^2")).toEqual({
      ok: false,
      error: "Enter only the number. The unit is already set: m/s^2.",
    });
  });
});

describe("normalizeAssessment", () => {
  it("treats an unknown or missing value as not graded", () => {
    expect(normalizeAssessment("CORRECT")).toBe("not_assessable");
    expect(normalizeAssessment(undefined)).toBe("not_assessable");
    expect(normalizeAssessment("wrong_method")).toBe("wrong_method");
  });
});

describe("canSeeReference", () => {
  it("hides the answer after one wrong attempt and shows it after two", () => {
    expect(canSeeReference(1, false)).toBe(false);
    expect(canSeeReference(2, false)).toBe(true);
    expect(canSeeReference(0, true)).toBe(true);
  });
});
