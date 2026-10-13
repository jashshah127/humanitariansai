import { DEFAULT_LABELS, normalizeVerification } from "./verification.ts";
import type { VerificationState } from "./verification.ts";
import styles from "./Badge.module.css";

export interface VerificationBadgeProps {
  /** The raw `verification` value from the server. Untrusted on purpose. */
  state: string | null | undefined;
  /** The server's `badge` text. Only used when the state is a known one. */
  label?: string | null;
}

/**
 * Shows whether an answer was verified. Rules from physics_mode_api.json:
 * - an unknown or missing state shows as "Unverified", never "Verified";
 * - a label that claims "Verified" is ignored unless the state really is verified;
 * - color is never the only signal: every state has its own icon and text.
 */
export function VerificationBadge({ state, label }: VerificationBadgeProps) {
  const normalized = normalizeVerification(state);
  const stateIsKnown = normalized === state;
  const labelClaimsVerified = !!label && /^\s*verified\b/i.test(label);

  const text =
    stateIsKnown && label && !(labelClaimsVerified && normalized !== "verified")
      ? label
      : DEFAULT_LABELS[normalized];

  return (
    <span className={styles.badge} data-state={normalized}>
      <BadgeIcon state={normalized} />
      <span>{text}</span>
    </span>
  );
}

function BadgeIcon({ state }: { state: VerificationState }) {
  return (
    <svg
      className={styles.icon}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {state === "verified" && (
        <>
          <circle cx="8" cy="8" r="6.5" />
          <path d="M5.25 8.25l1.9 1.9 3.6-4" />
        </>
      )}
      {state === "needs_review" && (
        <>
          <path d="M8 2.2l6.2 11H1.8z" />
          <path d="M8 6.5v3" />
          <circle cx="8" cy="11.4" r="0.6" fill="currentColor" stroke="none" />
        </>
      )}
      {state === "unverified" && (
        <>
          <circle cx="8" cy="8" r="6.5" />
          <path d="M6.3 6.3a1.8 1.8 0 1 1 2.5 1.6c-0.5 0.3-0.8 0.6-0.8 1.2v0.3" />
          <circle cx="8" cy="11.4" r="0.6" fill="currentColor" stroke="none" />
        </>
      )}
    </svg>
  );
}
