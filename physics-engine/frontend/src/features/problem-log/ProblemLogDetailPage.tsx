import { useEffect, useId, useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams } from "react-router";
import {
  DIFFICULTIES,
  DIFFICULTY_LABELS,
  GRADES,
  GRADE_LABELS,
  isUuid,
  problemLogStore,
  TagEditError,
} from "../../api/problemLog.ts";
import type {
  Difficulty,
  Grade,
  LogEntry,
  ProblemLogStore,
  TopicPair,
} from "../../api/problemLog.ts";
import { useAuth } from "../auth/AuthContext.ts";
import { VerificationBadge } from "../../design/components/Badge.tsx";
import { Button } from "../../design/components/Button.tsx";
import { Input, Select } from "../../design/components/Input.tsx";
import { AdminOnly } from "./AdminOnly.tsx";
import { formatExact, formatHour, TAG_SOURCE_LABELS } from "./display.ts";
import styles from "./problemLog.module.css";

/** /app/history/:id: one logged problem, with the tag-fixing form. */
export default function ProblemLogDetailPage({ store = problemLogStore }: { store?: ProblemLogStore }) {
  return (
    <AdminOnly store={store}>
      <Detail store={store} />
    </AdminOnly>
  );
}

type Load =
  | { status: "loading" }
  | { status: "error" }
  | { status: "missing" }
  | { status: "ready"; row: LogEntry; topics: TopicPair[] };

function Detail({ store }: { store: ProblemLogStore }) {
  const { id } = useParams();
  const valid = isUuid(id);
  const [load, setLoad] = useState<Load>(valid ? { status: "loading" } : { status: "missing" });
  const [attempt, setAttempt] = useState(0);
  const [saved, setSaved] = useState(false);
  const { session } = useAuth();

  useEffect(() => {
    if (!valid) return;
    let live = true;
    Promise.all([store.get(id), store.topics()]).then(
      ([row, topics]) => {
        if (live) setLoad(row ? { status: "ready", row, topics } : { status: "missing" });
      },
      (e: unknown) => {
        console.error("[problem log] get failed", e);
        if (live) setLoad({ status: "error" });
      },
    );
    return () => {
      live = false;
    };
  }, [store, id, valid, attempt]);

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <Link to="/app/history" className={styles.back}>
          ← All problem logs
        </Link>
      </header>

      {load.status === "loading" && <p className={styles.status}>Loading…</p>}

      {load.status === "error" && (
        <div role="alert" className={styles.notice}>
          <p>This problem couldn’t be loaded. Check your connection and try again.</p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              setLoad({ status: "loading" });
              setAttempt((n) => n + 1);
            }}
          >
            Try again
          </Button>
        </div>
      )}

      {load.status === "missing" && (
        <>
          <h1 className={styles.title}>Problem not found</h1>
          <p className={styles.status}>
            <Link to="/app/history">See all problems</Link>.
          </p>
        </>
      )}

      {load.status === "ready" && (
        <article>
          <h1 className={styles.title}>Logged problem</h1>
          <p className={styles.problem}>{load.row.problem_text}</p>

          <dl className={styles.facts}>
            <div>
              <dt>Asked</dt>
              <dd>
                <time dateTime={load.row.created_at}>{formatHour(load.row.created_at)}</time>
              </dd>
            </div>
            <div>
              <dt>Verification</dt>
              <dd>
                <VerificationBadge state={load.row.verification} />
              </dd>
            </div>
            <div>
              <dt>Personal details removed</dt>
              <dd>{load.row.redactions}</dd>
            </div>
            <div>
              <dt>Formula card</dt>
              <dd>{load.row.matched_card ?? "None"}</dd>
            </div>
            <div>
              <dt>Tags from</dt>
              <dd>
                {load.row.tag_source ? TAG_SOURCE_LABELS[load.row.tag_source] ?? load.row.tag_source : "Not tagged yet"}
                {load.row.tag_model ? ` (${load.row.tag_model})` : ""}
              </dd>
            </div>
            {load.row.tags_edited_at && (
              <div>
                <dt>Last edited</dt>
                <dd>
                  {formatExact(load.row.tags_edited_at)},{" "}
                  {load.row.tags_edited_by && load.row.tags_edited_by === session?.user.id
                    ? "by you"
                    : "by an admin"}
                </dd>
              </div>
            )}
          </dl>

          <TagForm
            // A fresh form after each save, filled from the row the database sent back.
            key={load.row.tags_edited_at ?? "never"}
            row={load.row}
            topics={load.topics}
            store={store}
            onSaved={(row) => {
              setLoad({ status: "ready", row, topics: load.topics });
              setSaved(true);
            }}
            onChange={() => setSaved(false)}
          />
          {saved && (
            <p role="status" className={styles.status}>
              Saved.
            </p>
          )}
        </article>
      )}
    </main>
  );
}

function TagForm({
  row,
  topics,
  store,
  onSaved,
  onChange,
}: {
  row: LogEntry;
  topics: TopicPair[];
  store: ProblemLogStore;
  onSaved: (row: LogEntry) => void;
  onChange: () => void;
}) {
  const [topic, setTopic] = useState(row.topic ?? "");
  const [subtopic, setSubtopic] = useState(row.subtopic ?? "");
  const [grade, setGrade] = useState<Grade | "">(row.grade_level ?? "");
  const [difficulty, setDifficulty] = useState<Difficulty | "">(row.difficulty ?? "");
  // Saving usually means "an admin looked at it", so the flag clears unless kept on.
  const [stillNeedsReview, setStillNeedsReview] = useState(false);
  const [note, setNote] = useState(row.review_reason ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reviewId = useId();

  const topicNames = [...new Set(topics.map((t) => t.topic))];
  const subtopics = topics.filter((t) => t.topic === topic).map((t) => t.subtopic);
  // A tagged row must keep a full topic/subtopic pair: the database refuses to clear it,
  // and refuses grade/difficulty on a row with no topic (see the migration's checks).
  const canSave = !!topic && !!subtopic && !saving;

  function touched<T>(setter: (v: T) => void) {
    return (v: T) => {
      setter(v);
      setError(null);
      onChange();
    };
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!canSave) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await store.updateTags(row.id, {
        topic,
        subtopic,
        grade_level: grade || null,
        difficulty: difficulty || null,
        needs_review: stillNeedsReview,
        review_reason: note.trim() || null,
      });
      onSaved(updated);
    } catch (err) {
      if (!(err instanceof TagEditError)) console.error("[problem log] save failed", err);
      setError(err instanceof TagEditError ? err.message : "The tags couldn’t be saved. Try again.");
      setSaving(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={(e) => void submit(e)}>
      <h2 className={styles.subtitle}>Tags</h2>
      {row.needs_review && (
        <p className={styles.notice}>
          <span className={styles.flag}>Needs review</span>
          {row.review_reason ?? "Flagged by the tagger."}
        </p>
      )}

      <div className={styles.fields}>
        <Select
          label="Topic"
          value={topic}
          onChange={(e) => {
            const next = e.target.value;
            const subs = topics.filter((t) => t.topic === next).map((t) => t.subtopic);
            touched(setTopic)(next);
            setSubtopic(subs.length === 1 ? (subs[0] ?? "") : "");
          }}
        >
          {!topic && <option value="">Choose a topic</option>}
          {topicNames.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </Select>
        <Select
          label="Subtopic"
          value={subtopic}
          disabled={!topic}
          onChange={(e) => touched(setSubtopic)(e.target.value)}
        >
          {!subtopic && <option value="">Choose a subtopic</option>}
          {subtopics.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </Select>
        <Select
          label="Grade level"
          value={grade}
          onChange={(e) => touched(setGrade)(e.target.value as Grade | "")}
        >
          <option value="">Not set</option>
          {GRADES.map((g) => (
            <option key={g} value={g}>
              {GRADE_LABELS[g]}
            </option>
          ))}
        </Select>
        <Select
          label="Difficulty"
          value={difficulty}
          onChange={(e) => touched(setDifficulty)(e.target.value as Difficulty | "")}
        >
          <option value="">Not set</option>
          {DIFFICULTIES.map((d) => (
            <option key={d} value={d}>
              {DIFFICULTY_LABELS[d]}
            </option>
          ))}
        </Select>
      </div>

      <Input
        label="Review note"
        value={note}
        placeholder="Why the tags were changed (optional)"
        onChange={(e) => touched(setNote)(e.target.value)}
      />

      <label htmlFor={reviewId} className={styles.check}>
        <input
          id={reviewId}
          type="checkbox"
          checked={stillNeedsReview}
          onChange={(e) => touched(setStillNeedsReview)(e.target.checked)}
        />
        Still needs review
      </label>

      {!topic || !subtopic ? (
        <p className={styles.status}>Choose a topic and subtopic to save.</p>
      ) : null}
      {error && (
        <p role="alert" className={styles.error}>
          {error}
        </p>
      )}

      <Button type="submit" disabled={!canSave} loading={saving}>
        Save tags
      </Button>
    </form>
  );
}