import { Link } from "react-router";
import { EmptyState } from "../design/components/EmptyState.tsx";
import styles from "./StatusPage.module.css";

export default function NotFoundPage() {
  return (
    <main className={styles.page}>
      <EmptyState
        headingLevel={1}
        title="Page not found"
        action={<Link to="/app">Go to the workspace</Link>}
      >
        <p>This address doesn’t match any page. Check the link, or start from the workspace.</p>
      </EmptyState>
    </main>
  );
}
