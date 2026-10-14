// Shared fetch wrapper. Converted from legacy/api.js; behaviour is unchanged.

const TOKEN_KEY = "pe_token";
const SESSION_KEY = "pe_session";

export function loadToken(): string {
  try {
    return localStorage.getItem(TOKEN_KEY) ?? "";
  } catch {
    return "";
  }
}

// Saved on every change, not on blur, so a paste-then-click is never lost.
export function saveToken(token: string): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Storage blocked: the token still works for this page load.
  }
}

// The contract requires session_id. One id per browser tab.
// It groups telemetry only; it is NOT a student identifier.
export function sessionId(): string {
  try {
    let id = sessionStorage.getItem(SESSION_KEY);
    if (!id) {
      id = crypto.randomUUID();
      sessionStorage.setItem(SESSION_KEY, id);
    }
    return id;
  } catch {
    return "web";
  }
}

export type ApiErrorKind = "auth" | "rate" | "http" | "network";

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly retryAfter: number | null;

  constructor(kind: ApiErrorKind, message: string, retryAfter: number | null = null) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.retryAfter = retryAfter;
  }
}

export async function postJson<T>(
  path: string,
  body: unknown,
  token: string,
  signal?: AbortSignal,
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") throw e;
    throw new ApiError("network", "Can't reach the server. Check that it's running.");
  }

  if (res.status === 401) {
    throw new ApiError(
      "auth",
      "Your access token is missing, expired, or wrong. Paste a fresh one from mint_token.py.",
    );
  }
  if (res.status === 429) {
    const wait = Number(res.headers.get("Retry-After")) || null;
    throw new ApiError("rate", "Too many requests right now.", wait);
  }
  if (!res.ok) {
    throw new ApiError("http", `The server returned an error (${res.status}).`);
  }
  return (await res.json()) as T;
}
