import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, useLocation } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { sampleHistory } from "../../api/history.ts";
import type { HistoryStore } from "../../api/history.ts";
import HistoryDetailPage from "./HistoryDetailPage.tsx";
import HistoryPage from "./HistoryPage.tsx";

function WorkspaceStub() {
  const location = useLocation();
  return (
    <p>
      workspace {location.search} {JSON.stringify(location.state)}
    </p>
  );
}

function open(url: string, store: HistoryStore) {
  const router = createMemoryRouter(
    [
      { path: "/app", element: <WorkspaceStub /> },
      { path: "/app/history", element: <HistoryPage store={store} /> },
      { path: "/app/history/:id", element: <HistoryDetailPage store={store} /> },
    ],
    { initialEntries: [url] },
  );
  render(<RouterProvider router={router} />);
  return router;
}

afterEach(() => vi.restoreAllMocks());

const failing: HistoryStore = {
  list: () => Promise.reject(new Error("down")),
  get: () => Promise.reject(new Error("down")),
  remove: () => Promise.reject(new Error("down")),
  save: () => Promise.reject(new Error("down")),
};

describe("HistoryPage", () => {
  it("lists the user's problems newest first", async () => {
    open("/app/history", sampleHistory());
    const items = await screen.findAllByRole("listitem");
    expect(items).toHaveLength(4);
    const [first] = items;
    if (!first) throw new Error("no items");
    expect(within(first).getByRole("link")).toHaveTextContent(/pulley/);
    expect(within(first).getByRole("link")).toHaveAttribute("href", "/app/history/1");
    expect(screen.getByText("Showing 4 of 4")).toBeInTheDocument();
  });

  it("filters by verification state and by text", async () => {
    open("/app/history", sampleHistory());
    await screen.findAllByRole("listitem");

    fireEvent.change(screen.getByLabelText("Verification"), { target: { value: "needs_review" } });
    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(screen.getByText(/spring with k = 500/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Verification"), { target: { value: "all" } });
    fireEvent.change(screen.getByLabelText("Search"), { target: { value: "PULLEY" } });
    expect(screen.getAllByRole("listitem")).toHaveLength(1);

    fireEvent.change(screen.getByLabelText("Search"), { target: { value: "no such problem" } });
    expect(screen.getByText(/No problems match/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(screen.getAllByRole("listitem")).toHaveLength(4);
  });

  it("an unknown verification value is never filed under Verified", async () => {
    open(
      "/app/history",
      sampleHistory([
        {
          id: 9,
          problem_text: "odd row",
          mode: "solve",
          verification: "verifiedish",
          answer: null,
          created_at: "2026-11-10T00:00:00Z",
        },
      ]),
    );
    await screen.findAllByRole("listitem");
    fireEvent.change(screen.getByLabelText("Verification"), { target: { value: "verified" } });
    expect(screen.queryAllByRole("listitem")).toHaveLength(0);
    fireEvent.change(screen.getByLabelText("Verification"), { target: { value: "unverified" } });
    expect(screen.getAllByRole("listitem")).toHaveLength(1);
  });

  it("shows an empty state", async () => {
    open("/app/history", sampleHistory([]));
    expect(await screen.findByText(/No problems yet/)).toBeInTheDocument();
  });

  it("shows an error with a retry, and the retry works", async () => {
    const store = sampleHistory();
    const list = vi
      .fn<HistoryStore["list"]>()
      .mockRejectedValueOnce(new Error("down"))
      .mockImplementation(() => store.list());
    vi.spyOn(console, "error").mockImplementation(() => {});
    open("/app/history", { ...store, list });
    expect(await screen.findByRole("alert")).toHaveTextContent(/couldn’t be loaded/);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findAllByRole("listitem")).toHaveLength(4);
  });
});

describe("HistoryDetailPage", () => {
  it("shows one problem with its saved answer", async () => {
    open("/app/history/1", sampleHistory());
    expect(await screen.findByText(/frictionless pulley/)).toBeInTheDocument();
    expect(screen.getByText("1.96")).toBeInTheDocument();
    expect(screen.getByText("47.04")).toBeInTheDocument();
  });

  it("reopens the problem in the workspace in the same mode", async () => {
    open("/app/history/2", sampleHistory());
    fireEvent.click(await screen.findByRole("button", { name: "Open in the workspace" }));
    const ws = await screen.findByText(/^workspace/);
    expect(ws).toHaveTextContent("?mode=tutor");
    expect(ws).toHaveTextContent("accelerates at 2.5 m/s^2");
  });

  it("deletes only after a confirm, then goes back to the list", async () => {
    const store = sampleHistory();
    open("/app/history/1", store);
    fireEvent.click(await screen.findByRole("button", { name: "Delete" }));
    expect(await store.get(1)).not.toBeNull(); // nothing gone yet
    fireEvent.click(screen.getByRole("button", { name: "Yes, delete" }));
    expect(await screen.findAllByRole("listitem")).toHaveLength(3);
    expect(await store.get(1)).toBeNull();
  });

  it("says not found for an id that doesn't exist", async () => {
    open("/app/history/999", sampleHistory());
    expect(await screen.findByText("Problem not found")).toBeInTheDocument();
  });

  it("says not found for an id that isn't a number, without asking the store", async () => {
    const get = vi.fn<HistoryStore["get"]>();
    open("/app/history/abc", { ...sampleHistory(), get });
    expect(await screen.findByText("Problem not found")).toBeInTheDocument();
    expect(get).not.toHaveBeenCalled();
  });

  it("shows an error when loading fails", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    open("/app/history/1", failing);
    expect(await screen.findByRole("alert")).toHaveTextContent(/couldn’t be loaded/);
  });

  it("keeps the problem and says so when delete fails", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const store = sampleHistory();
    open("/app/history/1", { ...store, remove: failing.remove });
    fireEvent.click(await screen.findByRole("button", { name: "Delete" }));
    fireEvent.click(screen.getByRole("button", { name: "Yes, delete" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/couldn’t be deleted/));
    expect(screen.getByText(/frictionless pulley/)).toBeInTheDocument();
  });
});