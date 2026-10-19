import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, within } from "@testing-library/react";
import { MAX_CHARS } from "./mode.ts";
import { ProblemInput } from "./ProblemInput.tsx";

function setup(value = "") {
  const onSubmit = vi.fn();
  const { container } = render(
    <ProblemInput value={value} onChange={() => {}} onSubmit={onSubmit} />,
  );
  return { box: within(container).getByLabelText("Your problem"), onSubmit, container };
}

describe("ProblemInput", () => {
  it("submits on Ctrl+Enter and Cmd+Enter, not on plain Enter", () => {
    const { box, onSubmit } = setup("x");
    fireEvent.keyDown(box, { key: "Enter" });
    expect(onSubmit).not.toHaveBeenCalled();
    fireEvent.keyDown(box, { key: "Enter", ctrlKey: true });
    fireEvent.keyDown(box, { key: "Enter", metaKey: true });
    expect(onSubmit).toHaveBeenCalledTimes(2);
  });

  it("shows the count under the limit", () => {
    const { box, container } = setup("hello");
    expect(box).toHaveAttribute("aria-invalid", "false");
    expect(container.textContent).toContain(`5 / ${MAX_CHARS}`);
  });

  it("marks the box invalid and says how far over the limit it is", () => {
    const { box, container } = setup("x".repeat(MAX_CHARS + 3));
    expect(box).toHaveAttribute("aria-invalid", "true");
    expect(container.textContent).toContain("3 characters over the limit");
  });
});