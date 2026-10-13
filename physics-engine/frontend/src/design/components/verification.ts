// The three states from physics_mode_api.json. Anything else the server sends
// (missing, misspelled, a new state we don't know yet) is treated as
// "unverified" -- never as "verified". This is the contract's core rule.

export const VERIFICATION_STATES = ["verified", "needs_review", "unverified"] as const;

export type VerificationState = (typeof VERIFICATION_STATES)[number];

export const DEFAULT_LABELS: Record<VerificationState, string> = {
  verified: "Verified",
  needs_review: "Needs review",
  unverified: "Unverified",
};

export function normalizeVerification(value: unknown): VerificationState {
  return (VERIFICATION_STATES as readonly unknown[]).includes(value)
    ? (value as VerificationState)
    : "unverified";
}
