import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Skeleton } from "./Skeleton.tsx";

describe("Skeleton", () => {
  it("is hidden from screen readers", () => {
    const { container } = render(<Skeleton />);
    expect(container.firstElementChild).toHaveAttribute("aria-hidden", "true");
  });

  it("takes a shape and a width", () => {
    const { container } = render(<Skeleton shape="pill" width="40%" />);
    const el = container.firstElementChild as HTMLElement;
    expect(el).toHaveAttribute("data-shape", "pill");
    expect(el.style.width).toBe("40%");
  });

  it("defaults to a full-width line", () => {
    const { container } = render(<Skeleton />);
    const el = container.firstElementChild as HTMLElement;
    expect(el).toHaveAttribute("data-shape", "line");
    expect(el.style.width).toBe("100%");
  });
});
