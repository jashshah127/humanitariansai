import type { SolveResponse } from "../../api/types.ts";
import { Card } from "../../design/components/Card.tsx";
import { VerificationBadge } from "../../design/components/Badge.tsx";
import { normalizeVerification } from "../../design/components/verification.ts";
import { AnswerList } from "./AnswerList.tsx";
import { CandidateList } from "./CandidateList.tsx";
import { HintLadder } from "./HintLadder.tsx";
import { WhyPanel } from "./WhyPanel.tsx";
import { Visualization } from "../visualization/Visualization.tsx";
import styles from "./result.module.css";

export interface ResultPanelProps {
  data: SolveResponse;
  /** True while a newer request is in flight; the old result stays visible but dimmed. */
  busy?: boolean;
}

/**
 * Renders one /solve response.
 * The badge is rendered here, once, before anything else -- not inside the
 * per-mode views -- so there is no code path that shows an answer without it.
 * `route` is never rendered (contract: debug only).
 */
export function ResultPanel({ data, busy = false }: ResultPanelProps) {
  const state = normalizeVerification(data.verification);
  const answer = data.answer && Object.keys(data.answer).length > 0 ? data.answer : null;
  const candidates = data.candidates ?? [];
  const hints = data.hints ?? [];
  const hasCandidates = candidates.length > 0;
  const hasHints = hints.length > 0;
  const outOfScope = data.needs_llm_completion && state === "unverified";
  // Only the badge would show. Say so instead of leaving an empty card.
  const nothingBack = !answer && !hasCandidates && !hasHints && !outOfScope;

  return (
    <Card>
      <article className={styles.result} data-state={state} aria-busy={busy}>
        <VerificationBadge state={data.verification} label={data.badge} />

        {/* needs_review also sets needs_llm_completion, but the candidate list
            explains that case better than a generic notice would. */}
        {outOfScope && (
          <p className={styles.notice}>
            This problem is outside what the engine can check. Any answer you get for it elsewhere
            is still unverified.
          </p>
        )}
        {nothingBack && (
          <p className={styles.empty}>
            No answer came back for this problem. Try writing it out in full, with every number and
            its unit, or start from one of the examples above.
          </p>
        )}
        {answer && <AnswerList answer={answer} latex={data.general_answer_latex} />}

        {/* Draws nothing unless the answer is verified and a diagram exists for its card. */}
        {answer && <Visualization data={data} />}

        {hasCandidates && <CandidateList candidates={candidates} />}

        {hasHints && <HintLadder hints={hints} />}

        <WhyPanel
          formula_used={data.formula_used}
          assumptions={data.assumptions}
          sources={data.sources}
          formula_latex={data.formula_latex}
          general_answer_latex={data.general_answer_latex}
        />

        {data.explanation && <p className={styles.explanation}>{data.explanation}</p>}

        {import.meta.env.DEV && typeof data.latency_ms === "number" && (
          <p className={styles.debug}>dev only: {Math.round(data.latency_ms)} ms</p>
        )}
      </article>
    </Card>
  );
}
