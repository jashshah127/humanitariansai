// Thin client for the contract in physics_mode_api.json.

const TOKEN_KEY = "pe_token";
const SESSION_KEY = "pe_session";

export function loadToken() {
  try { return localStorage.getItem(TOKEN_KEY) || ""; } catch { return ""; }
}

// Called on every change, not on blur -- avoids the old paste-then-click loss.
export function saveToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch { /* storage blocked: token still works for this page load */ }
}

// Contract marks session_id as required. One id per browser tab.
// It groups telemetry only; it is NOT a student identifier.
export function sessionId() {
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

export class ApiError extends Error {
  constructor(kind, message, retryAfter = null) {
    super(message);
    this.kind = kind;           // "auth" | "rate" | "http" | "network"
    this.retryAfter = retryAfter;
  }
}

export async function solve({ query, render, token }) {
  let res;
  try {
    res = await fetch("/solve", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ query, render, session_id: sessionId() }),
    });
  } catch {
    throw new ApiError("network", "Can't reach the server. Check that it's running.");
  }

  if (res.status === 401) {
    throw new ApiError("auth", "Token missing, expired, or wrong. Paste a fresh token from mint_token.py.");
  }
  if (res.status === 429) {
    const wait = Number(res.headers.get("Retry-After")) || null;
    throw new ApiError("rate", "Too many requests right now.", wait);
  }
  if (!res.ok) {
    throw new ApiError("http", `Server returned ${res.status}.`);
  }
  return res.json();
}