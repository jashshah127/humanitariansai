import { describe, expect, it } from "vitest";
import { fireEvent, render, within } from "@testing-library/react";
import type { SolveResponse } from "../../api/types.ts";
import { ResultPanel } from "./ResultPanel.tsx";

// Real engine output for the golden-set projectile (25 m/s at 40°).
const projectile: SolveResponse = {
  verification: "verified",
  badge: "Verified - solved symbolically",
  needs_llm_completion: false,
  explanation: "Solved using projectile motion.",
  route: "deterministic_script",
  card_id: "MECH-KIN-PROJ",
  knowns: { v0: 25, theta_deg: 40, g: 9.8 },
  answer: { t_flight: 3.2795, h_max: 13.175, range_: 62.807 },
  formula_used: "Projectile motion (equal launch/landing height)",
};

const tutor: SolveResponse = {
  verification: "verified",
  badge: "Verified - solved symbolically",
  needs_llm_completion: false,
  explanation: "Worked through as hints rather than a final answer.",
  route: "deterministic_script",
  answer: null,
  card_id: null,
  knowns: null,
  hints: ["List what you're given.", "The principle: Atwood machine.", "Worked result: a = 1.96"],
};

function article(data: SolveResponse) {
  const { container } = render(<ResultPanel data={data} />);
  const el = container.querySelector("article");
  if (!el) throw new Error("ResultPanel did not render an <article>");
  return within(el);
}

describe("ResultPanel in tutor render", () => {
  it("shows the hint ladder and no answer list", () => {
    const view = article(tutor);
    expect(view.getByRole("heading", { name: "Hints" })).toBeInTheDocument();
    expect(view.queryByRole("list", { name: "Answer" })).toBeNull();
    expect(view.queryByText(/a = 1\.96/)).toBeNull(); // last rung stays hidden
  });

  it("starts a new problem's ladder at the first hint", () => {
    // WorkspacePage gives each new result a new key. That key is what resets the ladder.
    const { container, rerender } = render(<ResultPanel key={1} data={tutor} />);
    fireEvent.click(within(container).getByRole("button", { name: "Show next hint" }));
    expect(within(container).getByText("2 of 3 shown")).toBeInTheDocument();

    rerender(<ResultPanel key={2} data={tutor} />);
    expect(within(container).getByText("1 of 3 shown")).toBeInTheDocument();
  });
});

describe("ResultPanel notices", () => {
  it("says the problem is outside the engine when unverified", () => {
    const view = article({
      ...tutor,
      verification: "unverified",
      badge: "Unverified - AI reasoning, not symbolically checked",
      needs_llm_completion: true,
      hints: null,
    });
    expect(view.getByText(/outside what the engine can check/)).toBeInTheDocument();
  });

  it("does not show that notice on needs_review (the candidate list explains it)", () => {
    const view = article({
      ...tutor,
      verification: "needs_review",
      badge: "Needs review - more than one principle applies",
      needs_llm_completion: true,
      hints: null,
      candidates: [{ principle: "Kinematics", applies_when: "constant a", answer: { v: 30 } }],
    });
    expect(view.queryByText(/outside what the engine can check/)).toBeNull();
  });
});

describe("ResultPanel diagrams", () => {
  it("draws the trajectory for a verified projectile answer", () => {
    expect(article(projectile).getByRole("img")).toHaveAccessibleName(/range 62\.807 m/);
  });

  it.each([
    ["needs_review", { verification: "needs_review" }],
    ["an unknown state", { verification: "Verified" }],
    ["a different card", { card_id: "MECH-DYN-ATWOOD" }],
  ])("draws nothing for %s", (_name, change) => {
    expect(article({ ...projectile, ...change }).queryByRole("img")).toBeNull();
  });
});
