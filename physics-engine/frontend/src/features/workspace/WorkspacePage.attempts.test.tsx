import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import WorkspacePage from "./WorkspacePage.tsx";

// End-to-end check of ui_guidance.grade: the attempt count lives in WorkspacePage,
// the hiding lives in GradeView. This test is the only place both run together.

const PROBLEM =
  "Two blocks of 4 kg and 6 kg hang from a frictionless pulley. Find the acceleration and tension.";

const parseReply = {
  gradable: true,
  reason: null,
  unknowns: [
    { name: "a", label: "linear acceleration", unit: "m/s^2" },
    { name: "T", label: "tension in the string", unit: "N" },
  ],
  given: [],
  parsed: { knowns: { m1: 4, m2: 6, g: 9.8 }, unknowns: ["a", "T"], topic_hint: "Mechanics" },
};

const wrongReply = {
  verification: "verified",
  badge: "Verified - graded against a symbolically checked answer",
  assessment: "wrong_value",
  per_quantity: {
    a: { submitted: 3, reference: 1.96, correct: false },
    T: { submitted: 47.04, reference: 47.04, correct: true },
  },
  reference_answer: { a: 1.96, T: 47.04 },
  feedback: "Not correct. Your value for a doesn't match the verified answer.",
  missing: [],
};

function json(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("WorkspacePage grade attempts", () => {
  it("hides the correct value after one wrong try and shows it after two", async () => {
    const fetchMock = vi.fn((url: string) =>
      Promise.resolve(json(url === "/parse" ? parseReply : wrongReply)),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { container } = render(
      <MemoryRouter initialEntries={["/app?mode=grade"]}>
        <WorkspacePage />
      </MemoryRouter>,
    );
    const view = within(container);

    fireEvent.change(view.getByRole("textbox", { name: /problem/i }), {
      target: { value: PROBLEM },
    });
    fireEvent.click(view.getByRole("button", { name: "Enter my answers" }));
    fireEvent.change(await view.findByLabelText("Linear acceleration (a)"), {
      target: { value: "3" },
    });
    fireEvent.change(view.getByLabelText("Tension in the string (T)"), {
      target: { value: "47.04" },
    });

    // Attempt 1: wrong, answer hidden.
    fireEvent.click(view.getByRole("button", { name: "Check my answers" }));
    await view.findByRole("heading", { name: "Not correct yet" });
    expect(container.textContent).not.toContain("Correct: 1.96");
    expect(view.getByText(/after one more try/)).toBeInTheDocument();

    // Attempt 2: wrong again, answer shown. Typed values were kept for the re-check.
    expect(view.getByLabelText("Linear acceleration (a)")).toHaveValue("3");
    fireEvent.click(view.getByRole("button", { name: "Check my answers" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    await waitFor(() => expect(container.textContent).toContain("Correct: 1.96 m/s²"));
  });
});
