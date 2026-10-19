import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, within } from "@testing-library/react";
import { ModeToggle } from "./ModeToggle.tsx";

describe("ModeToggle", () => {
  it("offers the three views and marks the current one", () => {
    const { container } = render(<ModeToggle value="tutor" onChange={() => {}} />);
    const view = within(container);
    expect(view.getAllByRole("radio")).toHaveLength(3);
    expect(view.getByRole("radio", { name: "Hints" })).toBeChecked();
    expect(view.getByRole("radio", { name: "Answer" })).not.toBeChecked();
  });

  it("reports the internal mode value, not the label", () => {
    const onChange = vi.fn();
    const { container } = render(<ModeToggle value="solve" onChange={onChange} />);
    fireEvent.click(within(container).getByRole("radio", { name: "Grade" }));
    expect(onChange).toHaveBeenCalledWith("grade");
  });

  it("cannot be changed while a request is running", () => {
    const { container } = render(<ModeToggle value="solve" onChange={() => {}} disabled />);
    for (const r of within(container).getAllByRole("radio")) expect(r).toBeDisabled();
  });
});