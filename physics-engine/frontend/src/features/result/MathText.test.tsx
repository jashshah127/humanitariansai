import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { MathText } from "./MathText.tsx";

describe("MathText", () => {
  it("renders the $...$ parts as math and keeps the rest as text", () => {
    const { container } = render(
      <MathText text="The relationship you need: $A = \pi r^{2}$; $EMF = A dBdt$" />,
    );
    expect(container.querySelectorAll(".katex")).toHaveLength(2);
    expect(container.textContent).toContain("The relationship you need:");
    expect(container.textContent).not.toContain("$");
  });

  it("shows plain text with no math unchanged", () => {
    const { container } = render(<MathText text="Worked result: a = 1.96" />);
    expect(container.querySelector(".katex")).toBeNull();
    expect(container.textContent).toBe("Worked result: a = 1.96");
  });

  it("shows an unpaired $ sign as plain text instead of guessing", () => {
    const { container } = render(<MathText text="Given: $r = 0.05. Find: EMF." />);
    expect(container.querySelector(".katex")).toBeNull();
    expect(container.textContent).toBe("Given: $r = 0.05. Find: EMF.");
  });
});