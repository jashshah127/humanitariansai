/** Joins class names, skipping empty ones: cx("a", false, undefined, "b") -> "a b". */
export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}
