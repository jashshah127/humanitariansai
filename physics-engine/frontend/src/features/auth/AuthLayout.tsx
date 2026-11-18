import type { ReactNode } from "react";
import { Card } from "../../design/components/Card.tsx";
import { usePageTitle } from "../../utils/usePageTitle.ts";
import styles from "./auth.module.css";

/** The shared frame for the login, sign-up and reset pages. */
export function AuthLayout({ title, children }: { title: string; children: ReactNode }) {
  usePageTitle(title);
  return (
    <main className={styles.page}>
      <p className={styles.brand}>Physics Engine</p>
      {/* h1: the card title is the main heading of these pages. */}
      <Card title={title} headingLevel={1} padding="lg">
        {children}
      </Card>
    </main>
  );
}
