// GET /me: who the signed-in caller is and their role (server.py api_me).
import { getJson } from "./client.ts";

/** What GET /me returns. Minted (operator) tokens have no Supabase account, so no role. */
export type MeResponse =
  | { kind: "supabase"; id: string; email: string; role: string | null }
  | { kind: "minted"; sub: string | null; role: null };

export function fetchMe(token: string, signal?: AbortSignal): Promise<MeResponse> {
  return getJson<MeResponse>("/me", token, signal);
}
