import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { SolveResponse } from "../../api/types.ts";
import { Visualization } from "./Visualization.tsx";

const res: SolveResponse = {
  verification: "verified",
  badge: "Verified",
  needs_llm_completion: false,
  explanation: "",
  route: "deterministic_script",
  card_id: "MECH-KIN-PROJ",
  knowns: { v0: 25, theta_deg: 40, g: 9.8 },
  answer: { t_flight: 3.2795, h_max: 13.175, range_: 62.807 },
};

describe("Visualization", () => {
  it("draws the trajectory with the engine's numbers in its accessible name", () => {
    render(<Visualization data={res} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/range 62\.807 m/);
    expect(img).toHaveAccessibleName(/maximum height 13\.175 m/);
  });

  it("moves the readout with the time slider", () => {
    render(<Visualization data={res} />);
    fireEvent.change(screen.getByLabelText("Time"), { target: { value: "100" } });
    // halfway through the flight: x = range/2, y = h_max
    expect(screen.getByText(/x = 31\.40\d* m/)).toBeInTheDocument();
    expect(screen.getByText(/y = 13\.175 m/)).toBeInTheDocument();
  });

  it("renders nothing when the answer is not verified", () => {
    const { container } = render(<Visualization data={{ ...res, verification: "needs_review" }} />);
    expect(container).toBeEmptyDOMElement();
  });
});
