import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, within } from "@testing-library/react";
import type { GivenValue, QuantitySpec } from "../../api/types.ts";
import { StudentAnswerForm } from "./StudentAnswerForm.tsx";

const unknowns: QuantitySpec[] = [
  { name: "a", label: "linear acceleration", unit: "m/s^2" },
  { name: "T", label: "tension in the string", unit: "N" },
];
const given: GivenValue[] = [
  { name: "m1", value: 4, unit: "kg", added: false },
  { name: "g", value: 9.8, unit: "m/s^2", added: true },
];

function Harness({ onCheck }: { onCheck: (a: Record<string, number>) => void }) {
  const [values, setValues] = useState<Record<string, string>>({});
  return (
    <StudentAnswerForm
      unknowns={unknowns}
      given={given}
      values={values}
      onChange={(n, v) => setValues((p) => ({ ...p, [n]: v }))}
      onCheck={onCheck}
      onReread={() => {}}
    />
  );
}

function setup() {
  const onCheck = vi.fn();
  const { container } = render(<Harness onCheck={onCheck} />);
  const view = within(container);
  const type = (label: RegExp, value: string) =>
    fireEvent.change(view.getByLabelText(label), { target: { value } });
  const check = () => fireEvent.click(view.getByRole("button", { name: "Check my answers" }));
  return { view, onCheck, type, check };
}

describe("StudentAnswerForm", () => {
  it("labels each box in words with its unit, not just the variable name", () => {
    const { view } = setup();
    expect(view.getByLabelText("Tension in the string (T)")).toBeTruthy();
    expect(view.getByText("In N")).toBeTruthy();
  });

  it("shows what the engine read, and marks added constants", () => {
    const { view } = setup();
    expect(view.getByText(/The engine read:/).textContent).toContain(
      "g = 9.8 m/s² (standard value)",
    );
  });

  it("sends numbers, not text", () => {
    const { onCheck, type, check } = setup();
    type(/acceleration/i, "1.96");
    type(/tension/i, "47.04");
    check();
    expect(onCheck).toHaveBeenCalledWith({ a: 1.96, T: 47.04 });
  });

  it("does not send when a box is empty or has a unit typed in", () => {
    const { view, onCheck, type, check } = setup();
    type(/acceleration/i, "1.96 m/s^2");
    check();
    expect(onCheck).not.toHaveBeenCalled();
    expect(view.getByText("Enter only the number. The unit is already set: m/s².")).toBeTruthy();
    expect(view.getByText("Enter a number.")).toBeTruthy();
  });
});
