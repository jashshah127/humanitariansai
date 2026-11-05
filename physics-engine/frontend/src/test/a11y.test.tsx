import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { ApiError } from "../api/client.ts";
import type { GradeResponse, QuantitySpec, SolveResponse } from "../api/types.ts";
import { GradeView } from "../features/grade/GradeView.tsx";
import { ResultPanel } from "../features/result/ResultPanel.tsx";
import { EmptyWorkspace } from "../features/workspace/EmptyWorkspace.tsx";
import { ErrorState } from "../features/workspace/ErrorState.tsx";
import NotFoundPage from "../pages/NotFoundPage.tsx";
import { axeIssues } from "./axe.ts";

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
  ...projectile,
  card_id: null,
  knowns: null,
  answer: null,
  hints: ["List what you're given.", "The principle: Atwood machine.", "Worked result: a = 1.96"],
};

const unknowns: QuantitySpec[] = [{ name: "a", label: "linear acceleration", unit: "m/s^2" }];

const wrong: GradeResponse = {
  verification: "verified",
  badge: "Verified - graded against a symbolically checked answer",
  assessment: "wrong_value",
  per_quantity: { a: { submitted: 3, reference: 1.96, correct: false } },
  reference_answer: { a: 1.96 },
  relationship_latex: "a = \\frac{g \\left(m_{1} - m_{2}\\right)}{m_{1} + m_{2}}",
  feedback: "Not correct. Your value for a doesn't match the verified answer.",
  missing: [],
};

describe("no WCAG A/AA issues", () => {
  it("result with an answer and a diagram", async () => {
    const { container } = render(<ResultPanel data={projectile} />);
    expect(await axeIssues(container)).toEqual([]);
  });

  it("hints", async () => {
    const { container } = render(<ResultPanel data={tutor} />);
    expect(await axeIssues(container)).toEqual([]);
  });

  it("graded answers", async () => {
    const { container } = render(
      <GradeView data={wrong} unknowns={unknowns} wrongAttempts={1} revealed={false} onReveal={() => {}} />,
    );
    expect(await axeIssues(container)).toEqual([]);
  });

  it("error", async () => {
    const { container } = render(
      <ErrorState error={new ApiError("network", "Can't reach the server.")} onRetry={() => {}} />,
    );
    expect(await axeIssues(container)).toEqual([]);
  });

  it("empty workspace", async () => {
    const { container } = render(<EmptyWorkspace mode="solve" />);
    expect(await axeIssues(container)).toEqual([]);
  });

  it("404 page", async () => {
    const { container } = render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>,
    );
    expect(await axeIssues(container)).toEqual([]);
  });
});