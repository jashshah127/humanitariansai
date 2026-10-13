import { useEffect, useState } from "react";
import { Button, Card, Input, TextArea, VerificationBadge } from "../design/components/index.ts";
import styles from "./DesignPreviewPage.module.css";

// Internal page: every token and component state on one screen.
// Used for design review, the Wk 5 accessibility pass and dark-mode checks.

type Theme = "system" | "light" | "dark";

const THEME_LABELS: Record<Theme, string> = { system: "System", light: "Light", dark: "Dark" };

const COLOR_GROUPS: Array<[string, string[]]> = [
  ["Brand", ["--color-brand", "--color-brand-hover"]],
  [
    "Text and surfaces",
    [
      "--color-bg",
      "--color-surface",
      "--color-surface-muted",
      "--color-text",
      "--color-text-muted",
      "--color-border",
      "--color-border-subtle",
      "--color-danger",
    ],
  ],
  [
    "Verification",
    [
      "--color-verified-bg",
      "--color-verified-text",
      "--color-review-bg",
      "--color-review-text",
      "--color-unverified-bg",
      "--color-unverified-text",
    ],
  ],
];

const TYPE_SCALE = ["--text-2xl", "--text-xl", "--text-lg", "--text-base", "--text-sm"];
const SPACING = [
  "--space-1",
  "--space-2",
  "--space-3",
  "--space-4",
  "--space-6",
  "--space-8",
  "--space-12",
];
const SAMPLE = "Two blocks of 4 kg and 6 kg hang from a frictionless pulley.";

export default function DesignPreviewPage() {
  const [theme, setTheme] = useState<Theme>("system");
  const [problem, setProblem] = useState("A car starts from rest and accelerates at 2.5 m/s².");

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
    return () => root.removeAttribute("data-theme");
  }, [theme]);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.h1}>Design system</h1>
        <div className={styles.row} role="group" aria-label="Theme">
          {(["system", "light", "dark"] as const).map((t) => (
            <Button
              key={t}
              size="sm"
              variant={theme === t ? "secondary" : "ghost"}
              aria-pressed={theme === t}
              onClick={() => setTheme(t)}
            >
              {THEME_LABELS[t]}
            </Button>
          ))}
        </div>
      </header>

      <section className={styles.section}>
        <h2 className={styles.h2}>Colors</h2>
        {COLOR_GROUPS.map(([group, names]) => (
          <div key={group} className={styles.group}>
            <h3 className={styles.h3}>{group}</h3>
            <div className={styles.swatches}>
              {names.map((name) => (
                <div key={name} className={styles.swatch}>
                  <div className={styles.chip} style={{ background: `var(${name})` }} />
                  <code className={styles.code}>{name}</code>
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>

      <section className={styles.section}>
        <h2 className={styles.h2}>Type scale</h2>
        {TYPE_SCALE.map((name) => (
          <div key={name} className={styles.typeRow}>
            <code className={styles.code}>{name}</code>
            <span style={{ fontSize: `var(${name})` }}>{SAMPLE}</span>
          </div>
        ))}
      </section>

      <section className={styles.section}>
        <h2 className={styles.h2}>Spacing</h2>
        {SPACING.map((name) => (
          <div key={name} className={styles.typeRow}>
            <code className={styles.code}>{name}</code>
            <span className={styles.bar} style={{ width: `var(${name})` }} />
          </div>
        ))}
      </section>

      <section className={styles.section}>
        <h2 className={styles.h2}>Buttons</h2>
        <div className={styles.row}>
          <Button>Solve</Button>
          <Button variant="secondary">Show next hint</Button>
          <Button variant="ghost">Cancel</Button>
        </div>
        <div className={styles.row}>
          <Button size="sm">Solve</Button>
          <Button size="sm" variant="secondary">
            Show next hint
          </Button>
          <Button size="sm" variant="ghost">
            Cancel
          </Button>
        </div>
        <div className={styles.row}>
          <Button disabled>Disabled</Button>
          <Button loading>Solving...</Button>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.h2}>Inputs</h2>
        <div className={styles.stack}>
          <Input label="Access token" placeholder="Paste a token" />
          <Input label="Student answer for a" hint="In m/s², numbers only." />
          <Input label="Student answer for T" defaultValue="abc" error="Enter a number." />
          <Input label="Disabled" disabled defaultValue="Can't edit this" />
          <TextArea
            label="Problem"
            value={problem}
            maxLength={500}
            onChange={(e) => setProblem(e.target.value)}
          />
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.h2}>Verification badges</h2>
        <div className={styles.row}>
          <VerificationBadge state="verified" />
          <VerificationBadge state="needs_review" />
          <VerificationBadge state="unverified" />
        </div>
        <p className={styles.note}>
          Unknown state from the server, with a label claiming &quot;Verified&quot;:
        </p>
        <div className={styles.row}>
          <VerificationBadge state="verfied" label="Verified" />
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.h2}>Cards</h2>
        <div className={styles.cards}>
          <Card title="Atwood machine">
            <p className={styles.muted}>
              Applies when the pulley is frictionless and the string is massless.
            </p>
          </Card>
          <Card title="Hints" padding="sm">
            <p className={styles.muted}>Small padding, for dense lists.</p>
          </Card>
        </div>
      </section>
    </div>
  );
}
