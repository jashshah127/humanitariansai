// Response and request shapes from engine/physics_mode_api.json.
// Keep this file in step with the contract: if the contract changes, change it here first.

export type RenderMode = "solve" | "tutor";

/** Numbers normally; strings when the problem was given in symbols (e.g. "m1*g/(m1+m2)"). */
export type AnswerValue = number | string;
export type AnswerMap = Record<string, AnswerValue>;

export interface Candidate {
  principle: string;
  applies_when: string;
  answer: AnswerMap | null;
}

export interface SolveRequest {
  query: string;
  session_id: string;
  render?: RenderMode;
  problem_id?: string | null;
}

export interface SolveResponse {
  /**
   * Typed as string, not VerificationState, on purpose: the value comes from the
   * network and must go through normalizeVerification() before it is trusted.
   */
  verification: string;
  badge: string;
  needs_llm_completion: boolean;
  explanation: string;
  /** Debug only. Never render to students. */
  route: string;
  answer?: AnswerMap | null;
  candidates?: Candidate[] | null;
  hints?: string[] | null;
  formula_used?: string | null;
  assumptions?: string[];
  /** variable -> the phrase it was read from. Can be null for injected constants. */
  sources?: Record<string, string | null>;
  latency_ms?: number;
  /** The card's equations as LaTeX. Empty in tutor mode (it would give hints away). */
  formula_latex?: string[];
  /** variable -> LaTeX of the rearranged general formula, e.g. "T = \\frac{...}{...}". */
  general_answer_latex?: Record<string, string> | null;
}
