import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, within } from "@testing-library/react";
import type { GradeResponse, QuantitySpec } from "../../api/types.ts";
import { GradeView } from "./GradeView.tsx";

const unknowns: QuantitySpec[] = [
  { name: "a", label: "linear acceleration", unit: "m/s^2" },
  { name: "T", label: "tension in the string", unit: "N" },
];

const wrong: GradeResponse = {
  verification: "verified",
  badge: "Verified - graded against a symbolically checked answer",
  assessment: "wrong_value",
  per_quantity: {
    a: { submitted: 3, reference: 1.96, correct: false },
    T: { submitted: 47.04, reference: 47.04, correct: true },
  },
  reference_answer: { a: 1.96, T: 47.04 },
  feedback: "Not correct. Your value for a doesn't match the verified answer.",
  missing: [],
};

function show(data: GradeResponse, wrongAttempts = 1, revealed = false, onReveal = () => {}) {
  const { container } = render(
    <GradeView
      data={data}
      unknowns={unknowns}
      wrongAttempts={wrongAttempts}
      revealed={revealed}
      onReveal={onReveal}
    />,
  );
  const article = container.querySelector("article");
  if (!article) throw new Error("GradeView did not render an <article>");
  return article;
}

describe("GradeView", () => {
  it("renders the badge first", () => {
    expect(show(wrong).firstElementChild?.hasAttribute("data-state")).toBe(true);
  });

  it("never shows Verified when the result was not graded", () => {
    const article = show({
      ...wrong,
      assessment: "not_assessable",
      verification: "verified", // a server bug must not turn into a green badge
      per_quantity: {},
    });
    expect(article.querySelector("[data-state]")?.getAttribute("data-state")).toBe("unverified");
  });

  it("treats a reply with no assessment as not graded", () => {
    const article = show({ ...wrong, assessment: "" });
    expect(article.querySelector("[data-state]")?.getAttribute("data-state")).toBe("unverified");
    expect(within(article).getByRole("heading").textContent).toBe("This answer wasn't graded");
  });

  it("hides the correct value after the first wrong attempt", () => {
    const article = show(wrong, 1);
    expect(article.textContent).not.toContain("1.96");
    expect(within(article).getByText(/after one more try/)).toBeTruthy();
  });

  it("shows the correct value after the second wrong attempt", () => {
    expect(show(wrong, 2).textContent).toContain("Correct: 1.96 m/s²");
  });

  it("shows the correct value when the student asks", () => {
    const onReveal = vi.fn();
    const article = show(wrong, 1, false, onReveal);
    fireEvent.click(within(article).getByRole("button", { name: "Show the correct answer" }));
    expect(onReveal).toHaveBeenCalledOnce();
    expect(show(wrong, 1, true).textContent).toContain("Correct: 1.96");
  });

  it("marks each value with a word, not only a color", () => {
    const rows = show(wrong).querySelectorAll("li");
    expect(rows[0]?.textContent).toContain("Wrong");
    expect(rows[1]?.textContent).toContain("Right");
  });

  it("lists a missing answer as missing", () => {
    const article = show({
      ...wrong,
      assessment: "incomplete",
      per_quantity: { a: { submitted: 1.96, reference: 1.96, correct: true } },
      missing: ["T"],
      feedback: "Every value you gave is right. Still missing: T.",
    });
    expect(article.querySelectorAll("li")[1]?.textContent).toContain("Missing");
    expect(within(article).queryByRole("button")).toBeNull();
  });
});
