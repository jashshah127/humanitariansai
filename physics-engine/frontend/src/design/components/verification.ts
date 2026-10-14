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

/**
 * Picks the text to show on the badge.
 *
 * The server's label is only used when (a) the state is one we know, and
 * (b) the label starts with that state's own default text, e.g.
 * "Needs review - more than one principle applies" for needs_review.
 * Anything else falls back to the default. This is an allow-list on purpose:
 * a block-list ("reject labels that start with Verified") lets through
 * labels like "✓ Verified" or "Symbolically verified" on the wrong state.
 */
export function badgeLabel(rawState: unknown, label: string | null | undefined): string {
  const state = normalizeVerification(rawState);
  if (state !== rawState || !label) return DEFAULT_LABELS[state];

  const text = label.trim();
  const prefix = DEFAULT_LABELS[state].toLowerCase();
  if (!text.toLowerCase().startsWith(prefix)) return DEFAULT_LABELS[state];

  // "Verified - solved symbolically" is fine; "Verifiedish" is not.
  const rest = text.slice(prefix.length);
  return rest === "" || !/^[a-z0-9]/i.test(rest) ? text : DEFAULT_LABELS[state];
}
