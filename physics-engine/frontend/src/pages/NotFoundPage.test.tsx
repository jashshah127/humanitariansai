import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it } from "vitest";
import NotFoundPage from "./NotFoundPage.tsx";

// Smoke test: proves Vitest, jsdom, Testing Library and the router are wired up.
describe("NotFoundPage", () => {
  it("links back to the workspace", () => {
    const router = createMemoryRouter([{ path: "*", element: <NotFoundPage /> }], {
      initialEntries: ["/nope"],
    });
    render(<RouterProvider router={router} />);
    expect(screen.getByRole("link", { name: "Go to the workspace" })).toHaveAttribute(
      "href",
      "/app",
    );
  });
});