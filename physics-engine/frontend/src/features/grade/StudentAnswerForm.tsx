import { useEffect, useId, useRef, useState } from "react";
import type { FormEvent } from "react";
import type { GivenValue, QuantitySpec } from "../../api/types.ts";
import { Button } from "../../design/components/Button.tsx";
import { Input } from "../../design/components/Input.tsx";
import { formatValue } from "../../utils/format.ts";
import { hasUnit, parseAnswer, prettyUnit, sentenceCase } from "./answer.ts";
import styles from "./grade.module.css";

interface Props {
  unknowns: QuantitySpec[];
  given: GivenValue[];
  /** What the student has typed, by quantity name. Owned by the parent so it survives a re-check. */
  values: Record<string, string>;
  onChange: (name: string, value: string) => void;
  onCheck: (answers: Record<string, number>) => void;
  /** Parse the problem again, for when the engine read it wrong. */
  onReread: () => void;
  busy?: boolean;
}

/** One box per asked-for quantity, labelled in words with the unit, never just "T". */
export function StudentAnswerForm({
  unknowns,
  given,
  values,
  onChange,
  onCheck,
  onReread,
  busy = false,
}: Props) {
  const headingId = useId();
  const formRef = useRef<HTMLFormElement>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  // Bumped on every failed submit, so focus moves even when the errors are unchanged.
  const [failedSubmits, setFailedSubmits] = useState(0);

  useEffect(() => {
    if (failedSubmits === 0) return;
    formRef.current?.querySelector<HTMLInputElement>('[aria-invalid="true"]')?.focus();
  }, [failedSubmits]);

  function submit(e: FormEvent) {
    e.preventDefault();
    const answers: Record<string, number> = {};
    const found: Record<string, string> = {};
    for (const u of unknowns) {
      const r = parseAnswer(values[u.name] ?? "", prettyUnit(u.unit));
      if (r.ok) answers[u.name] = r.value;
      else found[u.name] = r.error;
    }
    setErrors(found);
    if (Object.keys(found).length > 0) {
      setFailedSubmits((n) => n + 1);
      return;
    }
    onCheck(answers);
  }

  function change(name: string, value: string) {
    onChange(name, value);
    if (errors[name]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  }

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId} className={styles.heading}>
        Your answers
      </h2>

      {given.length > 0 && (
        <div className={styles.given}>
          <p className={styles.givenText}>
            The engine read: <GivenList given={given} />
          </p>
          <Button type="button" variant="ghost" size="sm" onClick={onReread} disabled={busy}>
            Read the problem again
          </Button>
        </div>
      )}

      <form ref={formRef} className={styles.form} onSubmit={submit} noValidate>
        <div className={styles.fields}>
          {unknowns.map((u) => (
            <Input
              key={u.name}
              label={`${sentenceCase(u.label)} (${u.name})`}
              hint={hasUnit(u.unit) ? `In ${prettyUnit(u.unit)}` : undefined}
              error={errors[u.name]}
              value={values[u.name] ?? ""}
              onChange={(e) => change(u.name, e.target.value)}
              inputMode="decimal"
              autoComplete="off"
              spellCheck={false}
            />
          ))}
        </div>
        <div>
          <Button type="submit" disabled={busy} aria-busy={busy}>
            {busy ? "Checking…" : "Check my answers"}
          </Button>
        </div>
      </form>
    </section>
  );
}

function GivenList({ given }: { given: GivenValue[] }) {
  return (
    <>
      {given.map((g, i) => (
        <span key={g.name}>
          {i > 0 && ", "}
          <var className={styles.varName}>{g.name}</var> = {formatValue(g.value)}
          {hasUnit(g.unit) && ` ${prettyUnit(g.unit)}`}
          {g.added && " (standard value)"}
        </span>
      ))}
      .
    </>
  );
}
