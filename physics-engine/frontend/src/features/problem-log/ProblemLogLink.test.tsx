import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { sampleProblemLog } from "../../api/problemLog.ts";
import { ProblemLogLink } from "./ProblemLogLink.tsx";

afterEach(() => vi.restoreAllMocks());

function show(store = sampleProblemLog()) {
  render(
    <MemoryRouter>
      <ProblemLogLink store={store} />
    </MemoryRouter>,
  );
}

describe("ProblemLogLink", () => {
  it("shows admins a link to the problem logs", async () => {
    show();
    expect(await screen.findByRole("link", { name: "Problem logs" })).toHaveAttribute(
      "href",
      "/app/history",
    );
  });

  it("shows nothing to a non-admin", async () => {
    const store = sampleProblemLog(undefined, { admin: false });
    const check = vi.spyOn(store, "isAdmin");
    show(store);
    await waitFor(() => expect(check).toHaveBeenCalled());
    await waitFor(() => Promise.resolve()); // let the answer arrive inside act()
    expect(screen.queryByRole("link", { name: "Problem logs" })).toBeNull();
  });

  it("shows nothing when the check fails", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => {});
    show({ ...sampleProblemLog(), isAdmin: () => Promise.reject(new Error("down")) });
    await waitFor(() => expect(console.warn).toHaveBeenCalled());
    expect(screen.queryByRole("link", { name: "Problem logs" })).toBeNull();
  });
});
