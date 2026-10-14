import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { MathFormula } from "./MathFormula.tsx";

describe("MathFormula", () => {
  it("renders LaTeX with KaTeX", () => {
    const { container } = render(<MathFormula latex="T = \frac{2 g m_{1} m_{2}}{m_{1} + m_{2}}" />);
    expect(container.querySelector(".katex")).not.toBeNull();
  });

  it("does not crash on bad LaTeX", () => {
    const { container } = render(<MathFormula latex="\frac{1}{" />);
    expect(container.textContent).not.toBe("");
  });

  it("does not render links from the input", () => {
    const { container } = render(<MathFormula latex="\href{https://example.com}{x}" />);
    expect(container.querySelector("a")).toBeNull();
  });
});
