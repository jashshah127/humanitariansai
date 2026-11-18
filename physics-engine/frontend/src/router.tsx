import { createBrowserRouter, Navigate } from "react-router";
import WorkspacePage from "./features/workspace/WorkspacePage.tsx";
import DesignPreviewPage from "./pages/DesignPreviewPage.tsx";
import NotFoundPage from "./pages/NotFoundPage.tsx";
import RouteErrorPage from "./pages/RouteErrorPage.tsx";
import LoginPage from "./features/auth/LoginPage.tsx";
import SignupPage from "./features/auth/SignupPage.tsx";
import ResetPasswordPage from "./features/auth/ResetPasswordPage.tsx";
import { RequireAuth } from "./features/auth/RequireAuth.tsx";
import ProblemLogPage from "./features/problem-log/ProblemLogPage.tsx";
import ProblemLogDetailPage from "./features/problem-log/ProblemLogDetailPage.tsx";

// // "/" sends everyone to the workspace at /app (the old app is retired).
// doesn't change while /app is being tested.
// "/app" is the new workspace (see docs/frontend-ia.md).
// Until server.py serves index.html for unknown paths (blocker B3),
// refreshing /app on the deployed site returns 404. Locally, Vite handles it.
export const router = createBrowserRouter([
  {
    // Catches a crash on any page below and shows RouteErrorPage instead.
    errorElement: <RouteErrorPage />,
    children: [
      { path: "/", element: <Navigate to="/app" replace /> },
      {
        path: "/app",
        element: (
          <RequireAuth>
            <WorkspacePage />
          </RequireAuth>
        ),
      },
        {
    path: "/app/history",
    element: (
      <RequireAuth>
        <ProblemLogPage />
      </RequireAuth>
    ),
  },
  {
    path: "/app/history/:id",
    element: (
      <RequireAuth>
        <ProblemLogDetailPage />
      </RequireAuth>
    ),
  },
      { path: "/login", element: <LoginPage /> },
      { path: "/signup", element: <SignupPage /> },
      { path: "/reset-password", element: <ResetPasswordPage /> },
      { path: "/design", element: <DesignPreviewPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
