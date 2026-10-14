import { describe, expect, it } from "vitest";
import { render, within } from "@testing-library/react";
import type { SolveResponse } from "../../api/types.ts";
import { ResultPanel } from "./ResultPanel.tsx";

const base: SolveResponse = {
  verification: "verified",
  badge: "Verified - solved symbolically",
  needs_llm_completion: false,
  explanation: "Solved using Atwood machine.",
  route: "deterministic_script",
  answer: { a: 1.96, T: 47.04 },
  formula_used: "Atwood machine",
  assumptions: ["massless string"],
  sources: { m1: "4 kg", m2: "6 kg", g: null },
};

function renderResult(overrides: Partial<SolveResponse> = {}) {
  const { container } = render(<ResultPanel data={{ ...base, ...overrides }} />);
  const article = container.querySelector("article");
  if (!article) throw new Error("ResultPanel did not render an <article>");
  return article;
}

describe("ResultPanel", () => {
  it.each(["verified", "needs_review", "unverified", "VERIFIED", "", "something_new"])(
    "always renders the badge first (state=%j)",
    (verification) => {
      const article = renderResult({ verification });
      expect(article.firstElementChild?.hasAttribute("data-state")).toBe(true);
    },
  );

  it("never shows 'Verified' when the state is unknown", () => {
    const article = renderResult({ verification: "Verified" });
    const badge = article.querySelector("[data-state]");
    expect(badge?.getAttribute("data-state")).toBe("unverified");
    expect(badge?.textContent).toBe("Unverified");
  });

  it("shows every candidate on needs_review", () => {
    const article = renderResult({
      verification: "needs_review",
      badge: "Needs review - more than one principle applies",
      needs_llm_completion: true,
      answer: null,
      candidates: [
        { principle: "Kinematics", applies_when: "constant acceleration", answer: { v: 30 } },
        { principle: "Spring energy", applies_when: "a spring is involved", answer: { v: 2.4 } },
      ],
    });
    const view = within(article);
    expect(view.getByText("Kinematics")).toBeTruthy();
    expect(view.getByText("Spring energy")).toBeTruthy();
  });

  it("skips sources that have no phrase", () => {
    const article = renderResult();
    expect(article.textContent).toContain("4 kg");
    expect(article.textContent).not.toContain("null");
  });

  it("never renders the internal route", () => {
    const article = renderResult();
    expect(article.textContent).not.toContain("deterministic_script");
  });
});
