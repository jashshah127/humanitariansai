import { describe, expect, it } from "vitest";
import { render, within } from "@testing-library/react";
import { AnswerList } from "./AnswerList.tsx";

describe("AnswerList", () => {
  it("rounds float noise to 5 significant figures", () => {
    const { container } = render(<AnswerList answer={{ T: 47.040000000000006 }} />);
    expect(container.textContent).toBe("T = 47.04");
  });

  it("shows a symbolic answer as math when LaTeX is sent", () => {
    const { container } = render(
      <AnswerList
        answer={{ T: "2*g*m1*m2/(m1 + m2)" }}
        latex={{ T: "T = \\frac{2 g m_{1} m_{2}}{m_{1} + m_{2}}" }}
      />,
    );
    expect(container.querySelector(".katex")).not.toBeNull();
  });

  it("falls back to the plain expression when no LaTeX is sent", () => {
    const { container } = render(<AnswerList answer={{ T: "2*g*m1*m2/(m1 + m2)" }} />);
    expect(container.querySelector(".katex")).toBeNull();
    expect(within(container).getByText("2*g*m1*m2/(m1 + m2)")).toBeInTheDocument();
  });
});
