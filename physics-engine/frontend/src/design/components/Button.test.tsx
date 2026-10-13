import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Button } from "./Button.tsx";

describe("Button", () => {
  it("is type=button by default so it never submits a form by accident", () => {
    render(<Button>Solve</Button>);
    expect(screen.getByRole("button", { name: "Solve" })).toHaveAttribute("type", "button");
  });

  it("calls onClick", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Solve</Button>);
    fireEvent.click(screen.getByRole("button", { name: "Solve" }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("blocks clicks and reports busy while loading", () => {
    const onClick = vi.fn();
    render(
      <Button loading onClick={onClick}>
        Solving...
      </Button>,
    );
    const button = screen.getByRole("button", { name: "Solving..." });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });
});
