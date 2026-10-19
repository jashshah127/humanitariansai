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

const tutorReply = {
  ...solveReply,
  answer: null,
  card_id: null,
  knowns: null,
  hints: ["List what you're given.", "The principle: Atwood machine.", "Worked result: a = 1.96"],
};

function json(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function open(url: string, reply: unknown) {
  const fetchMock = vi.fn<(url: string, init?: RequestInit) => Promise<Response>>(() =>
    Promise.resolve(json(reply)),
  );
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
  const sent = (i: number) => JSON.parse(String(fetchMock.mock.calls[i]?.[1]?.body));
  return { view, fetchMock, sent };
}

afterEach(() => vi.unstubAllGlobals());

describe("WorkspacePage in solve mode", () => {
  it("asks /solve for the answer and shows it under the badge", async () => {
    const { view, fetchMock, sent } = open("/app", solveReply);
    fireEvent.click(view.getByRole("button", { name: "Solve" }));

    expect(await view.findByRole("list", { name: "Answer" })).toHaveTextContent("a = 1.96");
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/solve");
    expect(sent(0)).toMatchObject({ query: PROBLEM, render: "solve" });
    expect(view.getByText("Verified - solved symbolically")).toBeInTheDocument();
  });
});

describe("WorkspacePage in tutor mode", () => {
  it("asks for render=tutor and shows hints, not the answer", async () => {
    const { view, sent } = open("/app?mode=tutor", tutorReply);
    fireEvent.click(view.getByRole("button", { name: "Get hints" }));

    expect(await view.findByRole("heading", { name: "Hints" })).toBeInTheDocument();
    expect(sent(0).render).toBe("tutor");
    expect(view.queryByRole("list", { name: "Answer" })).toBeNull();
  });

  it("restarts the hint ladder when a new result comes back", async () => {
    const { view, fetchMock } = open("/app?mode=tutor", tutorReply);
    fireEvent.click(view.getByRole("button", { name: "Get hints" }));
    fireEvent.click(await view.findByRole("button", { name: "Show next hint" }));
    expect(view.getByText("2 of 3 shown")).toBeInTheDocument();

    fireEvent.click(view.getByRole("button", { name: "Get hints" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(await view.findByText("1 of 3 shown")).toBeInTheDocument();
  });
});

describe("WorkspacePage mode switch", () => {
  it("changes the submit button to match the chosen view", () => {
    const { view } = open("/app", solveReply);
    fireEvent.click(view.getByRole("radio", { name: "Hints" }));
    expect(view.getByRole("button", { name: "Get hints" })).toBeInTheDocument();
    fireEvent.click(view.getByRole("radio", { name: "Grade" }));
    expect(view.getByRole("button", { name: "Enter my answers" })).toBeInTheDocument();
  });

  it("falls back to solve for an unknown ?mode=", () => {
    const { view } = open("/app?mode=cheat", solveReply);
    expect(view.getByRole("radio", { name: "Answer" })).toBeChecked();
  });
});
