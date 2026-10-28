import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { ApiError, isAbort } from "../../api/client.ts";
import { useAuth } from "../auth/AuthContext.ts";
import { grade, parseForGrading } from "../../api/grade.ts";
import { solve } from "../../api/solve.ts";
import type { GradeResponse, ParseResponse, SolveResponse } from "../../api/types.ts";
import { Button } from "../../design/components/Button.tsx";
import { isWrong, normalizeAssessment } from "../grade/answer.ts";
import { GradeSection } from "../grade/GradeSection.tsx";
import { ResultPanel } from "../result/ResultPanel.tsx";
import { ErrorState } from "./ErrorState.tsx";
import { ExampleChips } from "./ExampleChips.tsx";
import { MAX_CHARS, MODES, parseMode } from "./mode.ts";
import type { WorkspaceMode } from "./mode.ts";
import { ModeToggle } from "./ModeToggle.tsx";
import { ProblemInput } from "./ProblemInput.tsx";
import styles from "./workspace.module.css";

/** After this long, tell the student the wait is normal (cold start, provider retries). */
const SLOW_AFTER_MS = 8_000;

export default function WorkspacePage() {
  const [params, setParams] = useSearchParams();
  const mode = parseMode(params.get("mode"));

  const [query, setQuery] = useState("");
  const { token, session, signOut } = useAuth();
  const navigate = useNavigate();
  const [result, setResult] = useState<SolveResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(false);
  const [slow, setSlow] = useState(false);
  // A new key per result resets the hint ladder; otherwise a new problem
  // would open with the old problem's hint count. The error key restarts
  // the rate-limit countdown when the same kind of error comes back.
  const [resultId, setResultId] = useState(0);
  const [errorId, setErrorId] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  // What "Try again" repeats: the last request, whichever kind it was.
  const lastRequestRef = useRef<(() => void) | null>(null);

  // Grade mode. `setup` is the /parse reply for the problem text it was made from;
  // editing the problem makes it stale, and the answer boxes are hidden until the
  // student sets up again (the old boxes would belong to a different problem).
  const [setup, setSetup] = useState<{ query: string; data: ParseResponse } | null>(null);
  const [setupId, setSetupId] = useState(0);
  const [graded, setGraded] = useState<GradeResponse | null>(null);
  const [gradedId, setGradedId] = useState(0);
  const [wrongAttempts, setWrongAttempts] = useState(0);

  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    if (!loading) {
      setSlow(false);
      return;
    }
    const t = setTimeout(() => setSlow(true), SLOW_AFTER_MS);
    return () => clearTimeout(t);
  }, [loading]);

  const trimmed = query.trim();
  const setupCurrent = setup !== null && setup.query === trimmed;
  // In grade mode the button sets up answer boxes; once they exist for this exact text,
  // pressing it again would only spend another model call.
  const canSubmit =
    !!trimmed && trimmed.length <= MAX_CHARS && !loading && !(mode === "grade" && setupCurrent);
  const submitLabel = MODES.find((m) => m.value === mode)?.submit ?? "Solve";

  function changeMode(next: WorkspaceMode) {
    setParams(
      (prev) => {
        const p = new URLSearchParams(prev);
        p.set("mode", next);
        return p;
      },
      { replace: true },
    );
  }

  /**
   * Runs one request with the shared loading, slow-notice, cancel and error handling.
   * A new request cancels the one in flight. The old result stays on screen, dimmed,
   * until the new one arrives.
   */
  async function run(task: (signal: AbortSignal) => Promise<void>, onFail?: () => void) {
    lastRequestRef.current = () => void run(task, onFail);
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    try {
      await task(controller.signal);
    } catch (e) {
      if (isAbort(e)) return;
      onFail?.();
      if (e instanceof ApiError && e.kind === "auth") {
        void signOut().then(() => navigate("/login?reason=expired", { replace: true }));
        return;
      }
      setError(
        e instanceof ApiError ? e : new ApiError("network", "Something went wrong. Try again."),
      );
      setErrorId((n) => n + 1);
    } finally {
      if (abortRef.current === controller) setLoading(false);
    }
  }

  function submit() {
    if (!canSubmit) return;
    if (mode === "grade") {
      setUpGrading(trimmed);
      return;
    }
    const render = mode;
    void run(
      async (signal) => {
        const data = await solve({ query: trimmed, render, token, signal });
        setResult(data);
        setResultId((n) => n + 1);
      },
      () => setResult(null),
    );
  }

  function setUpGrading(text: string) {
    void run(async (signal) => {
      const data = await parseForGrading({ query: text, token, signal });
      setSetup({ query: text, data });
      setSetupId((n) => n + 1);
      setGraded(null);
      setWrongAttempts(0);
    });
  }

  function checkAnswers(answers: Record<string, number>) {
    if (!setup) return;
    const { query: text, data } = setup;
    void run(async (signal) => {
      const r = await grade({ query: text, parsed: data.parsed, answers, token, signal });
      if (isWrong(normalizeAssessment(r.assessment))) setWrongAttempts((n) => n + 1);
      setGraded(r);
      setGradedId((n) => n + 1);
    });
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div className={styles.account}>
          {session?.user.email && <span className={styles.accountEmail}>{session.user.email}</span>}
          <Button variant="ghost" size="sm" onClick={() => void signOut()}>
            Sign out
          </Button>
        </div>
        <h1 className={styles.title}>Physics Engine</h1>
        <p className={styles.lead}>
          Every answer says whether it was checked by a symbolic solver, or admits it wasn’t.
        </p>
      </header>

      <form
        className={styles.form}
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <ProblemInput value={query} onChange={setQuery} onSubmit={submit} />

        <div className={styles.controls}>
          <ModeToggle value={mode} onChange={changeMode} disabled={loading} />
          <Button type="submit" disabled={!canSubmit} aria-busy={loading}>
            {loading ? "Working…" : submitLabel}
          </Button>
        </div>

        <ExampleChips onPick={setQuery} />
      </form>

      <section className={styles.output} aria-live="polite">
        {loading && (
          <p className={styles.status}>
            {slow
              ? "Still working. The server may be starting up, which can take up to a minute."
              : "Working on it…"}
          </p>
        )}
        {error && (
          <ErrorState key={errorId} error={error} onRetry={() => lastRequestRef.current?.()} />
        )}
        {mode !== "grade" && result && <ResultPanel key={resultId} data={result} busy={loading} />}
        {mode === "grade" && setup && setupCurrent && (
          <GradeSection
            key={setupId}
            setup={setup.data}
            graded={graded}
            gradedId={gradedId}
            wrongAttempts={wrongAttempts}
            onCheck={checkAnswers}
            onReread={() => setUpGrading(setup.query)}
            busy={loading}
          />
        )}
        {mode === "grade" && setup && !setupCurrent && !loading && (
          <p className={styles.status}>
            The problem has changed. Press “{submitLabel}” to set up answer boxes for it.
          </p>
        )}
      </section>
    </main>
  );
}
