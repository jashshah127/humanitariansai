// Problem history: the signed-in user's own past problems (table public.problem_history).
//
// Kept apart from problems_log on purpose. That log is de-identified (no user id) and
// admin-only, so it can never answer "what did I ask?". This table is per-user, and its
// row rules let each user read, add and delete only their own rows.
//
// The browser talks to Supabase directly with the user's session. server.py is not
// involved, so saving history costs no model quota and needs no backend change.
import type { SupabaseClient } from "@supabase/supabase-js";
import { supabase } from "./supabase.ts";
import type { AnswerMap } from "./types.ts";

export type HistoryMode = "solve" | "tutor" | "grade";

/** One row of public.problem_history, as the browser sees it. */
export interface HistoryEntry {
  id: number;
  problem_text: string;
  mode: HistoryMode;
  /** From the network: run through normalizeVerification() before trusting it. */
  verification: string;
  answer: AnswerMap | null;
  /** ISO timestamp. */
  created_at: string;
}

/** What the app sends when saving. user_id and created_at are filled in by the database. */
export type NewHistoryEntry = Pick<HistoryEntry, "problem_text" | "mode" | "verification" | "answer">;

export interface HistoryStore {
  /** The signed-in user's own entries, newest first. */
  list(): Promise<HistoryEntry[]>;
  /** One entry, or null if it doesn't exist or isn't this user's. */
  get(id: number): Promise<HistoryEntry | null>;
  remove(id: number): Promise<void>;
  save(entry: NewHistoryEntry): Promise<void>;
}

const COLUMNS = "id, problem_text, mode, verification, answer, created_at";
/** Enough for a first version; search and filters run in the browser. Paginate when it isn't. */
const LIMIT = 200;

export function supabaseHistory(client: SupabaseClient): HistoryStore {
  const table = () => client.from("problem_history");
  return {
    async list() {
      const { data, error } = await table()
        .select(COLUMNS)
        .order("created_at", { ascending: false })
        .limit(LIMIT);
      if (error) throw new Error(error.message);
      return (data ?? []) as HistoryEntry[];
    },
    async get(id) {
      // Another user's id returns no row (the row rules hide it), so it reads as "not found".
      const { data, error } = await table().select(COLUMNS).eq("id", id).maybeSingle();
      if (error) throw new Error(error.message);
      return (data as HistoryEntry | null) ?? null;
    },
    async remove(id) {
      const { error } = await table().delete().eq("id", id);
      if (error) throw new Error(error.message);
    },
    async save(entry) {
      // Never send user_id: the database sets it from the session (default auth.uid()).
      const { error } = await table().insert(entry);
      if (error) throw new Error(error.message);
    },
  };
}

const SAMPLE: HistoryEntry[] = [
  {
    id: 1,
    problem_text:
      "Two blocks of 4 kg and 6 kg hang from a frictionless pulley. Find the acceleration and tension.",
    mode: "solve",
    verification: "verified",
    answer: { a: 1.96, T: 47.04 },
    created_at: "2026-11-14T15:20:00Z",
  },
  {
    id: 2,
    problem_text:
      "A car starts from rest and accelerates at 2.5 m/s^2 for 12 s. Find its final speed and distance.",
    mode: "tutor",
    verification: "verified",
    answer: null,
    created_at: "2026-11-13T10:05:00Z",
  },
  {
    id: 3,
    problem_text:
      "A 2 kg mass moves at 3 m/s and compresses a spring with k = 500 N/m. Find the speed.",
    mode: "solve",
    verification: "needs_review",
    answer: null,
    created_at: "2026-11-12T18:40:00Z",
  },
  {
    id: 4,
    problem_text:
      "A 0.5 kg mass on a spring with damping constant 1.2 kg/s. Find the damped frequency.",
    mode: "solve",
    verification: "unverified",
    answer: null,
    created_at: "2026-11-11T09:00:00Z",
  },
];

/** In-memory store for building and testing the UI. Nothing leaves the browser. */
export function sampleHistory(seed: HistoryEntry[] = SAMPLE): HistoryStore {
  let rows = seed.map((r) => ({ ...r }));
  let nextId = rows.reduce((max, r) => Math.max(max, r.id), 0) + 1;
  return {
    list: () =>
      Promise.resolve(
        [...rows].sort((a, b) => b.created_at.localeCompare(a.created_at)).map((r) => ({ ...r })),
      ),
    get: (id) => {
      const row = rows.find((r) => r.id === id);
      return Promise.resolve(row ? { ...row } : null);
    },
    remove: (id) => {
      rows = rows.filter((r) => r.id !== id);
      return Promise.resolve();
    },
    save: (entry) => {
      rows.push({ ...entry, id: nextId++, created_at: new Date().toISOString() });
      return Promise.resolve();
    },
  };
}

/**
 * The store the app uses. Sample data until VITE_HISTORY_SOURCE=supabase is set at
 * build time -- set it once problem_history exists on the hosted project (step 3).
 */
export const historyStore: HistoryStore =
  import.meta.env.VITE_HISTORY_SOURCE === "supabase" && supabase
    ? supabaseHistory(supabase)
    : sampleHistory();