import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { sampleProblemLog, TagEditError } from "../../api/problemLog.ts";
import type { ProblemLogStore, TagEdit } from "../../api/problemLog.ts";
import ProblemLogDetailPage from "./ProblemLogDetailPage.tsx";
import ProblemLogPage from "./ProblemLogPage.tsx";

afterEach(() => vi.restoreAllMocks());

const FLAGGED = "00000000-0000-4000-8000-000000000002";
const UNTAGGED_ROW = "00000000-0000-4000-8000-000000000005";

function open(url: string, store: ProblemLogStore) {
  const router = createMemoryRouter(
    [
      { path: "/app", element: <p>workspace</p> },
      { path: "/app/history", element: <ProblemLogPage store={store} /> },
      { path: "/app/history/:id", element: <ProblemLogDetailPage store={store} /> },
    ],
    { initialEntries: [url] },
  );
  render(<RouterProvider router={router} />);
  return router;
}

describe("admin gate", () => {
  it("a non-admin sees 'Admins only' and the log is never requested", async () => {
    const store = sampleProblemLog(undefined, { admin: false });
    const list = vi.spyOn(store, "list");
    open("/app/history", store);
    expect(await screen.findByText("Admins only")).toBeInTheDocument();
    expect(list).not.toHaveBeenCalled();
  });

  it("the detail page is gated too", async () => {
    const store = sampleProblemLog(undefined, { admin: false });
    const get = vi.spyOn(store, "get");
    open(`/app/history/${FLAGGED}`, store);
    expect(await screen.findByText("Admins only")).toBeInTheDocument();
    expect(get).not.toHaveBeenCalled();
  });

  it("a failed access check says so instead of showing an empty page", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const store = { ...sampleProblemLog(), isAdmin: () => Promise.reject(new Error("down")) };
    open("/app/history", store);
    expect(await screen.findByRole("alert")).toHaveTextContent(/couldn’t be checked/);
  });
});

describe("ProblemLogPage", () => {
  it("lists every logged problem newest first, with the review count", async () => {
    open("/app/history", sampleProblemLog());
    const items = await screen.findAllByRole("listitem");
    expect(items).toHaveLength(5);
    const [first] = items;
    if (!first) throw new Error("no items");
    expect(within(first).getByRole("link")).toHaveTextContent(/frictionless pulley/);
    expect(screen.getByText(/2 problems need review/)).toBeInTheDocument();
  });

  it("'Show them' filters to the review queue", async () => {
    open("/app/history", sampleProblemLog());
    fireEvent.click(await screen.findByRole("button", { name: "Show them" }));
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });

  it("filters by topic, including untagged rows, and by verification", async () => {
    open("/app/history", sampleProblemLog());
    await screen.findAllByRole("listitem");
    fireEvent.change(screen.getByLabelText("Topic"), { target: { value: "Mechanics" } });
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    fireEvent.change(screen.getByLabelText("Topic"), { target: { value: "untagged" } });
    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(screen.getByText("Not tagged", { selector: "span" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Topic"), { target: { value: "all" } });
    fireEvent.change(screen.getByLabelText("Verification"), { target: { value: "unverified" } });
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });

  it("says when nothing is logged yet", async () => {
    open("/app/history", sampleProblemLog([]));
    expect(await screen.findByText(/Nothing logged yet/)).toBeInTheDocument();
  });

  it("shows an error with a working retry", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const store = sampleProblemLog();
    const real = store.list.bind(store);
    const list = vi
      .fn<ProblemLogStore["list"]>()
      .mockRejectedValueOnce(new Error("down"))
      .mockImplementation(real);
    open("/app/history", { ...store, list });
    expect(await screen.findByRole("alert")).toHaveTextContent(/couldn’t be loaded/);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findAllByRole("listitem")).toHaveLength(5);
  });
});

describe("ProblemLogDetailPage", () => {
  it("shows the cleaned text, the facts and the review reason", async () => {
    open(`/app/history/${FLAGGED}`, sampleProblemLog());
    expect(await screen.findByText(/my email is \[EMAIL\]/)).toBeInTheDocument();
    expect(screen.getByText("MECH-DYN-ATWOOD")).toBeInTheDocument();
    expect(screen.getByText("model said E&M / Circuits")).toBeInTheDocument();
  });

  it("saves only the six editable columns and clears the review flag by default", async () => {
    const store = sampleProblemLog();
    const update = vi.spyOn(store, "updateTags");
    open(`/app/history/${FLAGGED}`, store);
    await screen.findByLabelText("Topic");
    fireEvent.change(screen.getByLabelText("Grade level"), {
      target: { value: "intro_undergrad" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save tags" }));
    expect(await screen.findByText("Saved.")).toBeInTheDocument();

    const sent = update.mock.calls[0]?.[1] as TagEdit;
    expect(Object.keys(sent).sort()).toEqual([
      "difficulty",
      "grade_level",
      "needs_review",
      "review_reason",
      "subtopic",
      "topic",
    ]);
    expect(sent).toMatchObject({ grade_level: "intro_undergrad", needs_review: false });
    expect(screen.getByText("Admin")).toBeInTheDocument(); // tag_source after the edit
    expect(screen.getByText(/Last edited/)).toBeInTheDocument();
  });

  it("changing the topic resets the subtopic to that topic's options", async () => {
    open(`/app/history/${FLAGGED}`, sampleProblemLog());
    await screen.findByLabelText("Topic");
    fireEvent.change(screen.getByLabelText("Topic"), { target: { value: "E&M" } });
    expect(screen.getByLabelText("Subtopic")).toHaveValue("");
    expect(screen.getByRole("button", { name: "Save tags" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Subtopic"), { target: { value: "Circuits" } });
    expect(screen.getByRole("button", { name: "Save tags" })).toBeEnabled();
    // "Other" has one subtopic, so it is picked automatically.
    fireEvent.change(screen.getByLabelText("Topic"), { target: { value: "Other" } });
    expect(screen.getByLabelText("Subtopic")).toHaveValue("Other");
  });

  it("an untagged row can't be saved until it has a topic and subtopic", async () => {
    open(`/app/history/${UNTAGGED_ROW}`, sampleProblemLog());
    await screen.findByLabelText("Topic");
    expect(screen.getByRole("button", { name: "Save tags" })).toBeDisabled();
    expect(screen.getByText(/Choose a topic and subtopic to save/)).toBeInTheDocument();
  });

  it("shows the database's refusal in plain words and keeps the form", async () => {
    const store = sampleProblemLog();
    open(`/app/history/${FLAGGED}`, {
      ...store,
      updateTags: () =>
        Promise.reject(new TagEditError("Those tags aren’t an allowed combination.")),
    });
    await screen.findByLabelText("Topic");
    fireEvent.click(screen.getByRole("button", { name: "Save tags" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/allowed combination/));
    expect(screen.getByRole("button", { name: "Save tags" })).toBeEnabled();
  });

  it("an unexpected save error gets a generic message", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const store = sampleProblemLog();
    open(`/app/history/${FLAGGED}`, {
      ...store,
      updateTags: () => Promise.reject(new Error("socket")),
    });
    await screen.findByLabelText("Topic");
    fireEvent.click(screen.getByRole("button", { name: "Save tags" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/couldn’t be saved/));
  });

  it("a malformed id says not found without asking the database", async () => {
    const store = sampleProblemLog();
    const get = vi.spyOn(store, "get");
    open("/app/history/42", store);
    expect(await screen.findByText("Problem not found")).toBeInTheDocument();
    expect(get).not.toHaveBeenCalled();
  });

  it("an unknown id says not found", async () => {
    open("/app/history/00000000-0000-4000-8000-0000000000ff", sampleProblemLog());
    expect(await screen.findByText("Problem not found")).toBeInTheDocument();
  });
});
