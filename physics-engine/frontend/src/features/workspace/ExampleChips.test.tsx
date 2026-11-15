import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { ExampleChips } from "./ExampleChips.tsx";
import { EXAMPLES } from "./examples.ts";

describe("ExampleChips", () => {
  it("shows one button per example", () => {
    render(<ExampleChips onPick={() => {}} />);
    expect(screen.getAllByRole("button")).toHaveLength(EXAMPLES.length);
  });

  it("puts the diagram examples in their own row", () => {
    render(<ExampleChips onPick={() => {}} />);
    const row = screen.getByText("Examples with a diagram:").closest("p")!;
    const labels = Array.from(row.querySelectorAll("button")).map((b) => b.textContent);
    expect(labels).toEqual(EXAMPLES.filter((ex) => ex.diagram).map((ex) => ex.label));
  });

  it.each(EXAMPLES.map((ex) => [ex.label, ex.text]))(
    "%s fills in its exact text",
    (label, text) => {
      const onPick = vi.fn();
      render(<ExampleChips onPick={onPick} />);
      fireEvent.click(screen.getByRole("button", { name: label }));
      expect(onPick).toHaveBeenCalledWith(text);
    },
  );
});
