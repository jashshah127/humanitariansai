// Supabase's error messages, reworded for students. Anything not listed is shown as is.
const FRIENDLY: [RegExp, string][] = [
  [/invalid login credentials/i, "That email and password don't match."],
  [/email not confirmed/i, "Confirm your email first. Check your inbox for the link."],
  [/rate limit|too many/i, "Too many emails were sent recently. Try again in an hour."],
  [/same.*password|different from the old/i, "Choose a password you haven't used before."],
  [/failed to fetch|network/i, "Can't reach the sign-in service. Check your connection."],
];

export function friendly(message: string): string {
  return FRIENDLY.find(([pattern]) => pattern.test(message))?.[1] ?? message;
}

export function messageOf(e: unknown): string {
  return e instanceof Error ? e.message : "Something went wrong. Try again.";
}
