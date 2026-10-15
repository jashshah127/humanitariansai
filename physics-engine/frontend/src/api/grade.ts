import { postJson, sessionId } from "./client.ts";
import type {
  GradeRequest,
  GradeResponse,
  ParsedProblem,
  ParseRequest,
  ParseResponse,
} from "./types.ts";

interface Common {
  token: string;
  signal?: AbortSignal;
}

/** Grade mode, step 1: what must the student answer? Never returns the answer. */
export function parseForGrading({
  query,
  token,
  signal,
}: Common & { query: string }): Promise<ParseResponse> {
  const body: ParseRequest = { query, session_id: sessionId() };
  return postJson<ParseResponse>("/parse", body, token, signal);
}

/**
 * Grade mode, step 2. Pass the `parsed` object from step 1 so the server doesn't
 * parse again (one model call, and the variable names can't change in between).
 */
export function grade({
  query,
  parsed,
  answers,
  token,
  signal,
}: Common & {
  query: string;
  parsed: ParsedProblem | null;
  answers: Record<string, number>;
}): Promise<GradeResponse> {
  const body: GradeRequest = {
    query,
    session_id: sessionId(),
    parsed,
    student_answer: answers,
  };
  return postJson<GradeResponse>("/grade", body, token, signal);
}
