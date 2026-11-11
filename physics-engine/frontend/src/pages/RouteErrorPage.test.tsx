import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import RouteErrorPage from "./RouteErrorPage.tsx";

function Boom(): never {
  throw new Error("boom");
}

// The crash is logged on purpose; keep the test output clean.
beforeEach(() => {
  vi.spyOn(console, "error").mockImplementation(() => {});
});
afterEach(() => vi.restoreAllMocks());

describe("RouteErrorPage", () => {
  it("replaces a crashed page with a way out", () => {
    const router = createMemoryRouter([
      { path: "/", element: <Boom />, errorElement: <RouteErrorPage /> },
    ]);
    render(<RouterProvider router={router} />);
    expect(
      screen.getByRole("heading", { level: 1, name: "This page stopped working" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reload the page" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to the workspace" })).toHaveAttribute(
      "href",
      "/app",
    );
  });

  it("shows the not-found page for a 404", async () => {
    const router = createMemoryRouter([
      {
        path: "/",
        loader: () => {
          throw new Response("Not found", { status: 404 });
        },
        element: <p>never shown</p>,
        errorElement: <RouteErrorPage />,
      },
    ]);
    render(<RouterProvider router={router} />);
    expect(await screen.findByRole("heading", { name: "Page not found" })).toBeInTheDocument();
  });
});
