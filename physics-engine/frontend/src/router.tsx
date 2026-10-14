import { createBrowserRouter } from "react-router";
import LegacyApp from "./legacy/App.jsx";
import WorkspacePage from "./features/workspace/WorkspacePage.tsx";
import DesignPreviewPage from "./pages/DesignPreviewPage.tsx";
import NotFoundPage from "./pages/NotFoundPage.tsx";

// "/" keeps the old app until the landing page lands in Wk 7, so the live site
// doesn't change while /app is being tested.
// "/app" is the new workspace (see docs/frontend-ia.md).
// Until server.py serves index.html for unknown paths (blocker B3),
// refreshing /app on the deployed site returns 404. Locally, Vite handles it.
export const router = createBrowserRouter([
  { path: "/", element: <LegacyApp /> },
  { path: "/app", element: <WorkspacePage /> },
  { path: "/design", element: <DesignPreviewPage /> },
  { path: "*", element: <NotFoundPage /> },
]);
