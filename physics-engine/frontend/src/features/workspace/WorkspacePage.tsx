import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router";
import { ApiError, isAbort, loadToken, saveToken } from "../../api/client.ts";
import { solve } from "../../api/solve.ts";
import type { RenderMode, SolveResponse } from "../../api/types.ts";
import { Button } from "../../design/components/Button.tsx";
import { ResultPanel } from "../result/ResultPanel.tsx";
import { ErrorState } from "./ErrorState.tsx";
import { ExampleChips } from "./ExampleChips.tsx";
import { MAX_CHARS, MODES, parseMode } from "./mode.ts";
import { ModeToggle } from "./ModeToggle.tsx";
import { ProblemInput } from "./ProblemInput.tsx";
import styles from "./workspace.module.css";

/** After this long, tell the student the wait is normal (cold start, provider retries). */
const SLOW_AFTER_MS = 8_000;

export default function WorkspacePage() {
  const [params, setParams] = useSearchParams();
  const mode = parseMode(params.get("mode"));

  const [query, setQuery] = useState("");
  const [token, setToken] = useState(loadToken);
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
  // Read once: if <details open> followed `token`, it would snap shut on the first keystroke.
  const [tokenOpenAtStart] = useState(() => !loadToken());

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
  const canSubmit = !!trimmed && trimmed.length <= MAX_CHARS && !loading;
  const submitLabel = MODES.find((m) => m.value === mode)?.submit ?? "Solve";

  function changeMode(next: RenderMode) {
    setParams(
      (prev) => {
        const p = new URLSearchParams(prev);
        p.set("mode", next);
        return p;
      },
      { replace: true },
    );
  }

  function changeToken(value: string) {
    const t = value.trim();
    setToken(t);
    saveToken(t);
  }

  async function submit() {
    if (!canSubmit) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    // The old result stays on screen, dimmed, until the new one arrives.
    try {
      const data = await solve({ query: trimmed, render: mode, token, signal: controller.signal });
      setResult(data);
      setResultId((n) => n + 1);
    } catch (e) {
      if (isAbort(e)) return;
      setResult(null);
      setError(
        e instanceof ApiError ? e : new ApiError("network", "Something went wrong. Try again."),
      );
      setErrorId((n) => n + 1);
    } finally {
      if (abortRef.current === controller) setLoading(false);
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Physics Engine</h1>
        <p className={styles.lead}>
          Every answer says whether it was checked by a symbolic solver, or admits it wasn’t.
        </p>
      </header>

      <form
        className={styles.form}
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <ProblemInput value={query} onChange={setQuery} onSubmit={() => void submit()} />

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
        {error && <ErrorState key={errorId} error={error} onRetry={() => void submit()} />}
        {result && <ResultPanel key={resultId} data={result} busy={loading} />}
      </section>

      <details className={styles.token} open={tokenOpenAtStart}>
        <summary>Access token (developer setup)</summary>
        <input
          className={styles.tokenInput}
          type="password"
          value={token}
          onChange={(e) => changeToken(e.target.value)}
          placeholder="Paste a token from mint_token.py"
          aria-label="Access token"
          autoComplete="off"
          spellCheck={false}
        />
      </details>
    </main>
  );
}
