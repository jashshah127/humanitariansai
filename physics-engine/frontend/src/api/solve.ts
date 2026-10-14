import { postJson, sessionId } from "./client.ts";
import type { RenderMode, SolveRequest, SolveResponse } from "./types.ts";

export interface SolveArgs {
  query: string;
  render: RenderMode;
  token: string;
  signal?: AbortSignal;
}

export function solve({ query, render, token, signal }: SolveArgs): Promise<SolveResponse> {
  const body: SolveRequest = { query, render, session_id: sessionId() };
  return postJson<SolveResponse>("/solve", body, token, signal);
}
