import { createBrowserRouter } from "react-router";
import LegacyApp from "./legacy/App.jsx";
import NotFoundPage from "./pages/NotFoundPage.tsx";

// The old App stays at "/" until the landing page lands in Wk 7.
// "/app" is the long-term home of the workspace (see docs/frontend-ia.md).
// Until server.py serves index.html for unknown paths (blocker B3),
// refreshing /app on the deployed site returns 404. Locally, Vite handles it.
export const router = createBrowserRouter([
  { path: "/", element: <LegacyApp /> },
  { path: "/app", element: <LegacyApp /> },
  { path: "*", element: <NotFoundPage /> },
]);