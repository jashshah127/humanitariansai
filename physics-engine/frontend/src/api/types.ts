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
  /** Id of the card that solved it. Solve render on the verified route only; null in tutor. */
  card_id?: string | null;
  /** The card's inputs as solved (number, or symbol name). Same rule as card_id. */
  knowns?: Record<string, AnswerValue> | null;
}

// ---------------------------------------------------------------- grade mode
// Two steps (see grade_mode in physics_mode_api.json): /parse says what to answer,
// /grade checks the student's numbers.

/** One quantity the student must answer. `name` is the key to send back. */
export interface QuantitySpec {
  name: string;
  /** Plain-language description, e.g. "tension in the string". */
  label: string;
  /** Unit the answer must be in, e.g. "m/s^2". Can be "" or "dimensionless". */
  unit: string;
}

/** A value the engine read from the problem, shown so a misread is caught early. */
export interface GivenValue {
  name: string;
  value: number;
  unit: string;
  /** A standard constant the student didn't state (e.g. g). */
  added: boolean;
}

/** Opaque to the UI: sent back to /grade unchanged so the problem is parsed once. */
export interface ParsedProblem {
  knowns: Record<string, number>;
  unknowns: string[];
  topic_hint: string | null;
}

export interface ParseRequest {
  query: string;
  session_id: string;
}

export interface ParseResponse {
  gradable: boolean;
  /** Plain-language reason when gradable is false. */
  reason?: string | null;
  unknowns: QuantitySpec[];
  given: GivenValue[];
  parsed: ParsedProblem | null;
}

export interface GradeRequest {
  query: string;
  session_id: string;
  parsed?: ParsedProblem | null;
  /** Numbers only: the server rejects strings with a 400. */
  student_answer: Record<string, number>;
}

export interface QuantityGrade {
  submitted: number;
  /** The correct value. Hidden by the UI until ui_guidance.grade allows it. */
  reference: AnswerValue;
  correct: boolean;
}

export interface GradeResponse {
  /** Untrusted, like SolveResponse.verification: normalize before use. */
  verification: string;
  badge: string;
  /** Untrusted: normalize with normalizeAssessment() before use. */
  assessment: string;
  per_quantity?: Record<string, QuantityGrade>;
  reference_answer?: AnswerMap | null;
  reference_formula?: string | null;
  /** Machine name of the matched mistake; the readable version is in `feedback`. */
  misconception?: string | null;
  missing?: string[];
  /** Never contains the correct value, so always safe to show. */
  feedback: string;
  confidence?: string;
}
