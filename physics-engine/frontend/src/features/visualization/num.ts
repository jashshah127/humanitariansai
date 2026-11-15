// Small number checks shared by the diagram guards.

export function finite(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

export function positive(v: unknown): v is number {
  return finite(v) && v > 0;
}

/**
 * True when a and b agree to a relative tolerance. Relative, not absolute, so
 * it works the same for 1e-7 s and 287601 N/C.
 */
export function close(a: number, b: number, relTol = 1e-6): boolean {
  const scale = Math.max(Math.abs(a), Math.abs(b));
  return scale === 0 || Math.abs(a - b) <= relTol * scale;
}
