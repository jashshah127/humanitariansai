import { describe, expect, it } from "vitest";
import { render, within } from "@testing-library/react";
import { WhyPanel } from "./WhyPanel.tsx";

describe("WhyPanel", () => {
  it("renders nothing when there is nothing to explain", () => {
    const { container } = render(<WhyPanel sources={{ g: null }} assumptions={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the principle, its conditions and what was read from the text", () => {
    const { container } = render(
      <WhyPanel
        formula_used="Atwood machine"
        assumptions={["massless string", "frictionless pulley"]}
        sources={{ m1: "4 kg", m2: "6 kg", g: null }}
      />,
    );
    const view = within(container);
    expect(view.getByText("Atwood machine")).toBeInTheDocument();
    expect(view.getByText("frictionless pulley")).toBeInTheDocument();
    expect(container.textContent).toContain("m1 from “4 kg”");
    expect(container.textContent).not.toContain("null");
  });

  it("renders each equation as math", () => {
    const { container } = render(
      <WhyPanel formula_latex={["T - g m_{1} = a m_{1}", "g m_{2} - T = a m_{2}"]} />,
    );
    expect(container.querySelectorAll(".katex")).toHaveLength(2);
  });
});
