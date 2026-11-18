// Admin-only problem history: public.problems_log, read and tag-fixed by admins.
//
// The database enforces the rules (migration 20261115220000_problems_log_admin_edits):
//   - only admins can read or update rows; signed-out visitors are refused
//   - a browser may change only six columns: topic, subtopic, grade_level, difficulty,
//     needs_review, review_reason -- never the text, the verification or the timestamps
//   - a trigger stamps tags_edited_by / tags_edited_at, and sets tag_source = 'admin'
//     (and clears tag_model) whenever the tags themselves change
// The text is the server's cleaned copy (emails, phones, links, IDs removed), created_at is
// rounded to the hour, and no row says who asked it.
import type { SupabaseClient } from "@supabase/supabase-js";
import { supabase } from "./supabase.ts";

// Same values as engine/classifier.py (GRADES, DIFFICULTIES) and the migration's checks.
export const GRADES = ["high_school", "intro_undergrad", "upper_undergrad", "graduate"] as const;
export const DIFFICULTIES = ["easy", "medium", "hard"] as const;
export type Grade = (typeof GRADES)[number];
export type Difficulty = (typeof DIFFICULTIES)[number];

export const GRADE_LABELS: Record<Grade, string> = {
  high_school: "High school",
  intro_undergrad: "Intro undergrad",
  upper_undergrad: "Upper undergrad",
  graduate: "Graduate",
};
export const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  easy: "Easy",
  medium: "Medium",
  hard: "Hard",
};

export type TagSource = "engine_card" | "llm" | "admin";

export interface TopicPair {
  topic: string;
  subtopic: string;
}

/** One row of public.problems_log. */
export interface LogEntry {
  id: string; // uuid
  problem_text: string;
  redactions: number;
  topic: string | null;
  subtopic: string | null;
  grade_level: Grade | null;
  difficulty: Difficulty | null;
  /** From the network: run through normalizeVerification() before trusting it. */
  verification: string;
  tag_model: string | null;
  tag_source: TagSource | null;
  needs_review: boolean;
  review_reason: string | null;
  matched_card: string | null;
  tags_edited_by: string | null;
  tags_edited_at: string | null;
  /** ISO timestamp, always a whole UTC hour. */
  created_at: string;
}

/** Exactly the columns a browser may change. Sending any other column is refused. */
export interface TagEdit {
  topic: string;
  subtopic: string;
  grade_level: Grade | null;
  difficulty: Difficulty | null;
  needs_review: boolean;
  review_reason: string | null;
}

/** A save the database refused for a reason the admin can act on. The message is for them. */
export class TagEditError extends Error {}

export interface ProblemLogStore {
  isAdmin(): Promise<boolean>;
  /** Newest first. */
  list(): Promise<LogEntry[]>;
  /** null when the row doesn't exist (or the caller can't read it). */
  get(id: string): Promise<LogEntry | null>;
  topics(): Promise<TopicPair[]>;
  /** Saves the tags; returns the row as the database now has it, stamps included. */
  updateTags(id: string, tags: TagEdit): Promise<LogEntry>;
}

// One literal string, not joined with +: supabase-js reads this text at the type level,
// and a joined string is just `string` to TypeScript, which breaks the row types.
const COLUMNS =
  "id, problem_text, redactions, topic, subtopic, grade_level, difficulty, verification, tag_model, tag_source, needs_review, review_reason, matched_card, tags_edited_by, tags_edited_at, created_at";
/** Filters run in the browser over the newest rows. Paginate when the log outgrows this. */
const LIMIT = 500;

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export function isUuid(s: string | undefined): s is string {
  return !!s && UUID.test(s);
}

function toError(error: { code?: string; message: string }): Error {
  // 23503: the topic/subtopic pair isn't in public.topics. 23514: a check failed
  // (grade, difficulty, or a half-filled pair).
  if (error.code === "23503" || error.code === "23514") {
    return new TagEditError(
      "Those tags aren’t an allowed combination. Pick a topic and subtopic from the lists.",
    );
  }
  // 42501: no privilege -- a column outside the six, or not signed in.
  if (error.code === "42501") return new TagEditError("Only admins can change tags.");
  return new Error(error.message);
}

export function supabaseProblemLog(client: SupabaseClient): ProblemLogStore {
  const table = () => client.from("problems_log");
  return {
    async isAdmin() {
      // The same function the database's own rules use, so the page and the rules agree.
      const { data, error } = await client.rpc("is_admin");
      if (error) throw new Error(error.message);
      return data === true;
    },
    async list() {
      const { data, error } = await table()
        .select(COLUMNS)
        .order("created_at", { ascending: false })
        .limit(LIMIT);
      if (error) throw new Error(error.message);
      return (data ?? []) as LogEntry[];
    },
    async get(id) {
      const { data, error } = await table().select(COLUMNS).eq("id", id).maybeSingle();
      if (error) throw new Error(error.message);
      return (data as LogEntry | null) ?? null;
    },
    async topics() {
      const { data, error } = await client
        .from("topics")
        .select("topic, subtopic")
        .order("topic")
        .order("subtopic");
      if (error) throw new Error(error.message);
      return (data ?? []) as TopicPair[];
    },
    async updateTags(id, tags) {
      const { data, error } = await table().update(tags).eq("id", id).select(COLUMNS).maybeSingle();
      if (error) throw toError(error);
      // A non-admin's update matches no rows: no error, just nothing back.
      if (!data)
        throw new TagEditError(
          "This problem couldn’t be changed. Check that you’re still an admin.",
        );
      return data as LogEntry;
    },
  };
}

// ---------------------------------------------------------------- sample data

const SAMPLE_TOPICS: TopicPair[] = (
  [
    ["Mechanics", "Kinematics"],
    ["Mechanics", "Dynamics"],
    ["Mechanics", "Work & Energy"],
    ["Mechanics", "Momentum"],
    ["Mechanics", "Rotation"],
    ["Mechanics", "Gravitation"],
    ["Mechanics", "Vibrations and Waves"],
    ["E&M", "Electrostatics"],
    ["E&M", "Circuits"],
    ["E&M", "Magnetism"],
    ["E&M", "Induction"],
    ["Thermodynamics", "Gas Laws"],
    ["Thermodynamics", "Calorimetry"],
    ["Thermodynamics", "Heat Engines"],
    ["Thermodynamics", "Entropy"],
    ["Thermodynamics", "Laws"],
    ["Other", "Other"],
  ] as [string, string][]
).map(([topic, subtopic]) => ({ topic, subtopic }));

const BLANK = {
  redactions: 0,
  tag_model: null,
  review_reason: null,
  matched_card: null,
  tags_edited_by: null,
  tags_edited_at: null,
};

const SAMPLE_ROWS: LogEntry[] = [
  {
    ...BLANK,
    id: "00000000-0000-4000-8000-000000000001",
    problem_text:
      "Two blocks of 4 kg and 6 kg hang from a frictionless pulley. Find the acceleration and tension.",
    topic: "Mechanics",
    subtopic: "Dynamics",
    grade_level: "intro_undergrad",
    difficulty: "easy",
    verification: "verified",
    tag_source: "engine_card",
    tag_model: "gemini-3.6-flash",
    needs_review: false,
    matched_card: "MECH-DYN-ATWOOD",
    created_at: "2026-11-15T15:00:00Z",
  },
  {
    ...BLANK,
    id: "00000000-0000-4000-8000-000000000002",
    problem_text: "A pulley problem: my email is [EMAIL]. Two masses of 3 kg and 5 kg. Find a.",
    redactions: 1,
    topic: "Mechanics",
    subtopic: "Dynamics",
    grade_level: "high_school",
    difficulty: "easy",
    verification: "verified",
    tag_source: "engine_card",
    tag_model: "gemini-3.6-flash",
    needs_review: true,
    review_reason: "model said E&M / Circuits",
    matched_card: "MECH-DYN-ATWOOD",
    created_at: "2026-11-15T14:00:00Z",
  },
  {
    ...BLANK,
    id: "00000000-0000-4000-8000-000000000003",
    problem_text:
      "Find the energy levels of an electron in a 1D infinite square well of width 1 nm.",
    topic: "Other",
    subtopic: "Other",
    grade_level: "upper_undergrad",
    difficulty: "medium",
    verification: "unverified",
    tag_source: "llm",
    tag_model: "gemini-3.6-flash",
    needs_review: true,
    review_reason: "outside the formula library",
    created_at: "2026-11-14T20:00:00Z",
  },
  {
    ...BLANK,
    id: "00000000-0000-4000-8000-000000000004",
    problem_text:
      "Two point charges of 3 microcoulombs are 0.05 m apart. Find the force between them.",
    topic: "E&M",
    subtopic: "Electrostatics",
    grade_level: "intro_undergrad",
    difficulty: "easy",
    verification: "verified",
    tag_source: "admin",
    needs_review: false,
    tags_edited_by: "sample-admin",
    tags_edited_at: "2026-11-14T18:42:00Z",
    created_at: "2026-11-14T17:00:00Z",
  },
  {
    ...BLANK,
    id: "00000000-0000-4000-8000-000000000005",
    problem_text:
      "A 0.5 kg mass on a spring with damping constant 1.2 kg/s. Find the damped frequency.",
    topic: null,
    subtopic: null,
    grade_level: null,
    difficulty: null,
    verification: "unverified",
    tag_source: null,
    needs_review: false,
    created_at: "2026-11-13T09:00:00Z",
  },
];

/** In-memory store for building and testing the UI. Mimics the database's rules and trigger. */
export function sampleProblemLog(
  rows: LogEntry[] = SAMPLE_ROWS,
  { admin = true, editor = "sample-admin" }: { admin?: boolean; editor?: string } = {},
): ProblemLogStore {
  let data = rows.map((r) => ({ ...r }));
  const copy = (r: LogEntry) => ({ ...r });
  return {
    isAdmin: () => Promise.resolve(admin),
    list: () =>
      Promise.resolve(
        admin ? [...data].sort((a, b) => b.created_at.localeCompare(a.created_at)).map(copy) : [],
      ),
    get: (id) => {
      const row = admin ? data.find((r) => r.id === id) : undefined;
      return Promise.resolve(row ? copy(row) : null);
    },
    topics: () => Promise.resolve(SAMPLE_TOPICS.map((t) => ({ ...t }))),
    updateTags: (id, tags) => {
      const old = data.find((r) => r.id === id);
      if (!admin || !old) {
        return Promise.reject(
          new TagEditError("This problem couldn’t be changed. Check that you’re still an admin."),
        );
      }
      if (!SAMPLE_TOPICS.some((t) => t.topic === tags.topic && t.subtopic === tags.subtopic)) {
        return Promise.reject(
          new TagEditError(
            "Those tags aren’t an allowed combination. Pick a topic and subtopic from the lists.",
          ),
        );
      }
      const tagsChanged =
        tags.topic !== old.topic ||
        tags.subtopic !== old.subtopic ||
        tags.grade_level !== old.grade_level ||
        tags.difficulty !== old.difficulty;
      const next: LogEntry = {
        ...old,
        ...tags,
        ...(tagsChanged ? { tag_source: "admin" as const, tag_model: null } : {}),
        tags_edited_by: editor,
        tags_edited_at: new Date().toISOString(),
      };
      data = data.map((r) => (r.id === id ? next : r));
      return Promise.resolve(copy(next));
    },
  };
}

/**
 * The store the app uses. Sample data until VITE_HISTORY_SOURCE=supabase is set at build
 * time (frontend/.env.local for dev, Render's build environment for the site).
 */
export const problemLogStore: ProblemLogStore =
  import.meta.env.VITE_HISTORY_SOURCE === "supabase" && supabase
    ? supabaseProblemLog(supabase)
    : sampleProblemLog();
