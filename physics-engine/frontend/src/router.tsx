import { createBrowserRouter, Navigate } from "react-router";
import WorkspacePage from "./features/workspace/WorkspacePage.tsx";
import DesignPreviewPage from "./pages/DesignPreviewPage.tsx";
import NotFoundPage from "./pages/NotFoundPage.tsx";
import LoginPage from "./features/auth/LoginPage.tsx";
import SignupPage from "./features/auth/SignupPage.tsx";
import ResetPasswordPage from "./features/auth/ResetPasswordPage.tsx";
import { RequireAuth } from "./features/auth/RequireAuth.tsx";

// // "/" sends everyone to the workspace at /app (the old app is retired).
// doesn't change while /app is being tested.
// "/app" is the new workspace (see docs/frontend-ia.md).
// Until server.py serves index.html for unknown paths (blocker B3),
// refreshing /app on the deployed site returns 404. Locally, Vite handles it.
export const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/app" replace /> },
  {
    path: "/app",
    element: (
      <RequireAuth>
        <WorkspacePage />
      </RequireAuth>
    ),
  },
  { path: "/login", element: <LoginPage /> },
  { path: "/signup", element: <SignupPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  { path: "/design", element: <DesignPreviewPage /> },
  { path: "*", element: <NotFoundPage /> },
]);
