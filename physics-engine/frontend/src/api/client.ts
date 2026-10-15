// Shared fetch wrapper. Converted from legacy/api.js, plus a request timeout.

const TOKEN_KEY = "pe_token";
const SESSION_KEY = "pe_session";

/**
 * How long to wait before giving up on one request.
 * Long on purpose: a Render free-tier server can take close to a minute to wake up,
 * and the engine retries the model provider a few times before falling back.
 */
export const REQUEST_TIMEOUT_MS = 90_000;

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

export type ApiErrorKind = "auth" | "rate" | "timeout" | "http" | "network";

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

/** True when a request was cancelled on purpose (a newer request, or the page closing). */
export function isAbort(e: unknown): boolean {
  return e instanceof DOMException && e.name === "AbortError";
}

function httpMessage(status: number): string {
  if (status === 400) {
    return "The engine couldn't read what was sent. Check that every answer is a plain number.";
  }
  if (status === 503) {
    return "The engine couldn't finish this problem. This is usually temporary; try again in a minute.";
  }
  // server.py never sends a 500 itself (it catches every error). In development a 500
  // comes from Vite's proxy when it can't reach server.py on :8000.
  if (status === 500 && import.meta.env.DEV) {
    return "Can't reach the engine. Check that server.py is running on port 8000.";
  }
  return `Something went wrong on the server (error ${status}).`;
}

export async function postJson<T>(
  path: string,
  body: unknown,
  token: string,
  signal?: AbortSignal,
  timeoutMs: number = REQUEST_TIMEOUT_MS,
): Promise<T> {
  // One controller for both reasons to stop: the caller cancelled, or we timed out.
  // (AbortSignal.any would be shorter but is missing from older Safari.)
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const onCallerAbort = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener("abort", onCallerAbort);

  try {
    let res: Response;
    try {
      res = await fetch(path, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
    } catch (e) {
      if (timedOut) {
        throw new ApiError("timeout", "The engine took too long to answer. Try again in a minute.");
      }
      if (isAbort(e)) throw e;
      throw new ApiError("network", "Can't reach the server. Check your connection and try again.");
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
    if (!res.ok) throw new ApiError("http", httpMessage(res.status));

    try {
      return (await res.json()) as T;
    } catch {
      throw new ApiError("http", "The server sent a reply this page couldn't read.");
    }
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", onCallerAbort);
  }
}
