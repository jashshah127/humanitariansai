import { Link } from "react-router";
import styles from "./NotFoundPage.module.css";
import { usePageTitle } from "../utils/usePageTitle.ts";

export default function NotFoundPage() {
      usePageTitle("Page not found");
  return (
    <main className={styles.page}>
      <p className={styles.brand}>Physics Engine</p>
      <h1 className={styles.title}>Page not found</h1>
      <p className={styles.lead}>This address doesn’t match any page.</p>
      <Link className={styles.link} to="/app">
        Go to the workspace
      </Link>
    </main>
  );
}
