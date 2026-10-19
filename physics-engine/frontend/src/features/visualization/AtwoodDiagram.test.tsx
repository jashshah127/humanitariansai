import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import type { SolveResponse } from "../../api/types.ts";
import { Visualization } from "./Visualization.tsx";

const res: SolveResponse = {
  verification: "verified",
  badge: "Verified",
  needs_llm_completion: false,
  explanation: "",
  route: "deterministic_script",
  card_id: "MECH-DYN-ATWOOD",
  knowns: { m1: 4, m2: 6, g: 9.8 },
  answer: { a: 1.9600000000000002, T: 47.040000000000006 },
};

describe("Atwood diagram", () => {
  it("is chosen for the Atwood card and states the engine's numbers", () => {
    render(<Visualization data={res} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/m1 = 4 kg, m2 = 6 kg/);
    expect(img).toHaveAccessibleName(/Tension 47\.04 N on both sides/);
    expect(img).toHaveAccessibleName(/m2 accelerates down and m1 up at 1\.96 m\/s²/);
  });

  it("points the heavier side down", () => {
    render(<Visualization data={res} />);
    expect(screen.getByTestId("accel-m2")).toHaveAttribute("data-direction", "down");
    expect(screen.getByTestId("accel-m1")).toHaveAttribute("data-direction", "up");
  });

  it("flips when m1 is heavier", () => {
    render(
      <Visualization
        data={{
          ...res,
          knowns: { m1: 6, m2: 4, g: 9.8 },
          answer: { a: -1.9600000000000002, T: 47.040000000000006 },
        }}
      />,
    );
    expect(screen.getByTestId("accel-m1")).toHaveAttribute("data-direction", "down");
    expect(screen.getByTestId("accel-m2")).toHaveAttribute("data-direction", "up");
  });

  it("draws no acceleration arrows for equal masses", () => {
    render(
      <Visualization
        data={{ ...res, knowns: { m1: 5, m2: 5, g: 9.8 }, answer: { a: 0, T: 49 } }}
      />,
    );
    expect(screen.queryByTestId("accel-m1")).toBeNull();
    expect(screen.getByRole("img")).toHaveAccessibleName(/neither accelerates/);
  });

  it("never prints a weight as a number (it would not be verified)", () => {
    const { container } = render(<Visualization data={res} />);
    expect(container.textContent).not.toContain("39.2"); // 4 × 9.8
    expect(container.textContent).not.toContain("58.8"); // 6 × 9.8
    expect(container.textContent).toContain("m₁g");
  });

  it("draws nothing when the numbers break Newton's second law", () => {
    const { container } = render(<Visualization data={{ ...res, answer: { a: 1.96, T: 50 } }} />);
    expect(container).toBeEmptyDOMElement();
  });
});
