import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import WorkspacePage from "./WorkspacePage.tsx";

const PROBLEM = "Two blocks of 4 kg and 6 kg hang from a frictionless pulley. Find a and T.";

const solveReply = {
  verification: "verified",
  badge: "Verified - solved symbolically",
  needs_llm_completion: false,
  explanation: "Solved using Atwood machine.",
  route: "deterministic_script",
  answer: { a: 1.96, T: 47.04 },
  formula_used: "Atwood machine",
  card_id: "MECH-DYN-ATWOOD",
  knowns: { m1: 4, m2: 6, g: 9.8 },
};

function json(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

/** A request that never answers, so the page stays in its loading state. */
const never = () => new Promise<Response>(() => {});

function open(url: string, fetchMock: unknown) {
  vi.stubGlobal("fetch", fetchMock);
  const { container } = render(
    <MemoryRouter initialEntries={[url]}>
      <WorkspacePage />
    </MemoryRouter>,
  );
  const view = within(container);
  fireEvent.change(view.getByRole("textbox", { name: /problem/i }), {
    target: { value: PROBLEM },
  });
  return view;
}

afterEach(() => vi.unstubAllGlobals());

describe("WorkspacePage loading states", () => {
  it("shows a skeleton and a text status while the first answer loads", async () => {
    const view = open("/app", vi.fn(never));
    fireEvent.click(view.getByRole("button", { name: "Solve" }));

    expect(await view.findByTestId("result-skeleton")).toBeInTheDocument();
    // Screen readers rely on the text status; the skeleton is hidden from them.
    expect(view.getByText("Working on it…")).toBeInTheDocument();
  });

  it("keeps the old answer, not a skeleton, while the next one loads", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => Promise.resolve(json(solveReply)))
      .mockImplementation(never);
    const view = open("/app", fetchMock);

    fireEvent.click(view.getByRole("button", { name: "Solve" }));
    expect(await view.findByRole("list", { name: "Answer" })).toBeInTheDocument();

    fireEvent.click(view.getByRole("button", { name: "Solve" }));
    await waitFor(() => expect(view.getByRole("button", { name: "Working…" })).toBeInTheDocument());
    expect(view.queryByTestId("result-skeleton")).toBeNull();
    expect(view.getByRole("list", { name: "Answer" })).toBeInTheDocument();
  });

  it("shows a skeleton while grade mode sets up the answer boxes", async () => {
    const view = open("/app?mode=grade", vi.fn(never));
    fireEvent.click(view.getByRole("button", { name: "Enter my answers" }));
    expect(await view.findByTestId("result-skeleton")).toBeInTheDocument();
  });
});
