import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, within } from "@testing-library/react";
import type { GradeResponse, ParseResponse } from "../../api/types.ts";
import { GradeSection } from "./GradeSection.tsx";

const setup: ParseResponse = {
  gradable: true,
  reason: null,
  unknowns: [
    { name: "a", label: "linear acceleration", unit: "m/s^2" },
    { name: "T", label: "tension in the string", unit: "N" },
  ],
  given: [{ name: "m1", value: 4, unit: "kg", added: false }],
  parsed: { knowns: { m1: 4, m2: 6, g: 9.8 }, unknowns: ["a", "T"], topic_hint: "Mechanics" },
};

const wrong: GradeResponse = {
  verification: "verified",
  badge: "Verified - graded against a symbolically checked answer",
  assessment: "wrong_value",
  per_quantity: {
    a: { submitted: 3, reference: 1.96, correct: false },
    T: { submitted: 47.04, reference: 47.04, correct: true },
  },
  reference_answer: { a: 1.96, T: 47.04 },
  feedback: "Not correct.",
  missing: [],
};

function props(over: Partial<Parameters<typeof GradeSection>[0]> = {}) {
  return {
    setup,
    graded: null,
    gradedId: 0,
    wrongAttempts: 0,
    onCheck: vi.fn(),
    onReread: vi.fn(),
    ...over,
  };
}

describe("GradeSection", () => {
  it("refuses to grade an ungradable problem, as unverified, with the reason", () => {
    const p = props({
      setup: { ...setup, gradable: false, reason: "More than one principle fits.", parsed: null },
    });
    const { container } = render(<GradeSection {...p} />);
    const view = within(container);
    expect(container.querySelector("[data-state]")?.getAttribute("data-state")).toBe("unverified");
    expect(view.getByText("More than one principle fits.")).toBeInTheDocument();
    expect(view.queryByRole("button", { name: "Check my answers" })).toBeNull();

    fireEvent.click(view.getByRole("button", { name: "Read the problem again" }));
    expect(p.onReread).toHaveBeenCalledOnce();
  });

  it("shows answer boxes and no verdict before the first check", () => {
    const { container } = render(<GradeSection {...props()} />);
    const view = within(container);
    expect(view.getByLabelText("Linear acceleration (a)")).toBeInTheDocument();
    expect(view.queryByRole("heading", { name: /Correct|Not correct/ })).toBeNull();
  });

  it("keeps what the student typed when a result comes back", () => {
    const p = props();
    const { container, rerender } = render(<GradeSection key="p1" {...p} />);
    const view = within(container);
    fireEvent.change(view.getByLabelText("Linear acceleration (a)"), { target: { value: "3" } });

    rerender(<GradeSection key="p1" {...p} graded={wrong} gradedId={1} wrongAttempts={1} />);
    expect(view.getByLabelText("Linear acceleration (a)")).toHaveValue("3");
    expect(view.getByRole("heading", { name: "Not correct yet" })).toBeInTheDocument();
  });

  it("clears typed values for a new problem (new key)", () => {
    const p = props();
    const { container, rerender } = render(<GradeSection key="p1" {...p} />);
    const view = within(container);
    fireEvent.change(view.getByLabelText("Linear acceleration (a)"), { target: { value: "3" } });

    rerender(<GradeSection key="p2" {...p} />);
    expect(view.getByLabelText("Linear acceleration (a)")).toHaveValue("");
  });

  it("reveals the correct value when the student asks, even on the first wrong try", () => {
    const { container } = render(
      <GradeSection {...props({ graded: wrong, gradedId: 1, wrongAttempts: 1 })} />,
    );
    const view = within(container);
    expect(container.textContent).not.toContain("Correct: 1.96");
    fireEvent.click(view.getByRole("button", { name: "Show the correct answer" }));
    expect(container.textContent).toContain("Correct: 1.96 m/s²");
  });
});