import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import WorkspacePage from "./WorkspacePage.tsx";

const PROBLEM =
  "Two blocks of 4 kg and 6 kg hang from a frictionless pulley. Find the acceleration and tension.";

const parseReply = {
  gradable: true,
  reason: null,
  unknowns: [
    { name: "a", label: "linear acceleration", unit: "m/s^2" },
    { name: "T", label: "tension in the string", unit: "N" },
  ],
  given: [{ name: "m1", value: 4, unit: "kg", added: false }],
  parsed: { knowns: { m1: 4, m2: 6, g: 9.8 }, unknowns: ["a", "T"], topic_hint: "Mechanics" },
};

const gradeReply = {
  verification: "verified",
  badge: "Verified - graded against a symbolically checked answer",
  assessment: "correct",
  per_quantity: {
    a: { submitted: 1.96, reference: 1.96, correct: true },
    T: { submitted: 47.04, reference: 47.04, correct: true },
  },
  reference_answer: { a: 1.96, T: 47.04 },
  feedback: "Correct.",
  missing: [],
};

function json(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("WorkspacePage in grade mode", () => {
  it("parses once, then grades with the parsed problem, and never calls /solve", async () => {
    const fetchMock = vi.fn((url: string) =>
      Promise.resolve(json(url === "/parse" ? parseReply : gradeReply)),
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
      target: { value: "1.96" },
    });
    fireEvent.change(view.getByLabelText("Tension in the string (T)"), {
      target: { value: "47.04" },
    });
    // Same text again: setting up again would only cost another model call.
    expect(
      (view.getByRole("button", { name: "Enter my answers" }) as HTMLButtonElement).disabled,
    ).toBe(true);

    fireEvent.click(view.getByRole("button", { name: "Check my answers" }));
    await view.findByRole("heading", { name: "Correct" });

    const urls = fetchMock.mock.calls.map((c) => c[0]);
    expect(urls).toEqual(["/parse", "/grade"]);
    const gradeCall = fetchMock.mock.calls[1] as unknown as [string, RequestInit];
    const sent = JSON.parse(String(gradeCall[1].body));
    expect(sent.parsed).toEqual(parseReply.parsed);
    expect(sent.student_answer).toEqual({ a: 1.96, T: 47.04 });
  });

  it("hides the answer boxes when the problem text changes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(json(parseReply))),
    );
    const { container } = render(
      <MemoryRouter initialEntries={["/app?mode=grade"]}>
        <WorkspacePage />
      </MemoryRouter>,
    );
    const view = within(container);
    const box = view.getByRole("textbox", { name: /problem/i });
    fireEvent.change(box, { target: { value: PROBLEM } });
    fireEvent.click(view.getByRole("button", { name: "Enter my answers" }));
    await view.findByLabelText("Linear acceleration (a)");

    fireEvent.change(box, { target: { value: PROBLEM + " Use g = 10." } });
    await waitFor(() => expect(view.queryByLabelText("Linear acceleration (a)")).toBeNull());
    expect(view.getByText(/The problem has changed/)).toBeTruthy();
  });
});
