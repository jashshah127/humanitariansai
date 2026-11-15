import type { ReactNode } from "react";
import { Card } from "../../design/components/Card.tsx";
import styles from "./auth.module.css";

/** The shared frame for the login, sign-up and reset pages. */
export function AuthLayout({ title, children }: { title: string; children: ReactNode }) {
  return (
    <main className={styles.page}>
      <p className={styles.brand}>Physics Engine</p>
      <Card title={title} headingLevel={2} padding="lg">
        {children}
      </Card>
    </main>
  );
}
