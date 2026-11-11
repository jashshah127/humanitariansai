import { isRouteErrorResponse, Link, useRouteError } from "react-router";
import { Button } from "../design/components/Button.tsx";
import { EmptyState } from "../design/components/EmptyState.tsx";
import NotFoundPage from "./NotFoundPage.tsx";
import styles from "./StatusPage.module.css";

function details(error: unknown): string {
  if (error instanceof Error) return error.stack ?? error.message;
  return String(error);
}

/**
 * Shown when a page crashes while rendering, instead of React Router's default
 * developer screen. Students get a way out; the details go to the console
 * (and, in dev only, onto the page).
 */
export default function RouteErrorPage() {
  const error = useRouteError();
  if (isRouteErrorResponse(error) && error.status === 404) return <NotFoundPage />;

  console.error(error);

  return (
    <main className={styles.page}>
      <EmptyState
        headingLevel={1}
        title="This page stopped working"
        action={
          <>
            <Button type="button" onClick={() => window.location.reload()}>
              Reload the page
            </Button>
            {/* A full page load, not an in-app move: the app itself may be what broke. */}
            <Link to="/app" reloadDocument>
              Go to the workspace
            </Link>
          </>
        }
      >
        <p>Something went wrong while showing this page. Reloading usually fixes it.</p>
      </EmptyState>
      {import.meta.env.DEV && <pre className={styles.details}>{details(error)}</pre>}
    </main>
  );
}
