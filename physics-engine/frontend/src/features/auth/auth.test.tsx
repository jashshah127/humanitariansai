import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import type { Session } from "@supabase/supabase-js";
import { describe, expect, it, vi } from "vitest";
import { AuthContext, signedOut } from "./AuthContext.ts";
import type { AuthValue } from "./AuthContext.ts";
import LoginPage from "./LoginPage.tsx";
import { RequireAuth } from "./RequireAuth.tsx";
import ResetPasswordPage from "./ResetPasswordPage.tsx";

const fakeSession = { access_token: "tok", user: { email: "a@test.dev" } } as unknown as Session;

function renderAt(
  path: string,
  auth: Partial<AuthValue>,
  routes?: { path: string; element: ReactNode }[],
) {
  const value: AuthValue = { ...signedOut, configured: true, ...auth };
  const router = createMemoryRouter(
    routes ?? [
      { path: "/login", element: <LoginPage /> },
      { path: "/reset-password", element: <ResetPasswordPage /> },
      {
        path: "/app",
        element: (
          <RequireAuth>
            <p>workspace</p>
          </RequireAuth>
        ),
      },
    ],
    { initialEntries: [path] },
  );
  render(
    <AuthContext.Provider value={value}>
      <RouterProvider router={router} />
    </AuthContext.Provider>,
  );
  return router;
}

describe("RequireAuth", () => {
  it("sends a signed-out user to /login", async () => {
    const router = renderAt("/app", {});
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
  });

  it("shows the page to a signed-in user", () => {
    renderAt("/app", { session: fakeSession, token: "tok" });
    expect(screen.getByText("workspace")).toBeInTheDocument();
  });
});

describe("LoginPage", () => {
  it("signs in with the typed email and password", async () => {
    const signIn = vi.fn().mockResolvedValue(undefined);
    // /app is a plain page here: the fake signIn doesn't create a session for RequireAuth.
    const router = renderAt("/login", { signIn }, [
      { path: "/login", element: <LoginPage /> },
      { path: "/app", element: <p>workspace</p> },
    ]);
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: " a@test.dev " } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret123" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(signIn).toHaveBeenCalledWith("a@test.dev", "secret123"));
    await waitFor(() => expect(router.state.location.pathname).toBe("/app"));
  });

  it("shows the error when sign-in fails", async () => {
    const signIn = vi.fn().mockRejectedValue(new Error("That email and password don't match."));
    renderAt("/login", { signIn });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@test.dev" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("don't match");
  });
});

describe("ResetPasswordPage", () => {
  it("asks for an email when there is no reset link", () => {
    renderAt("/reset-password", {});
    expect(screen.getByRole("button", { name: "Send reset link" })).toBeInTheDocument();
  });

  it("asks for a new password after a reset link signs the user in", () => {
    renderAt("/reset-password", { recoveryLink: true, session: fakeSession, token: "tok" });
    expect(screen.getByRole("button", { name: "Save new password" })).toBeInTheDocument();
  });

  it("says the link failed when it was refused", () => {
    renderAt("/reset-password", { linkError: "Email link is invalid or has expired" });
    expect(screen.getByRole("alert")).toHaveTextContent("expired or was already used");
  });
});
