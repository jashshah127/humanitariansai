import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, postJson } from "./client.ts";

function reply(status: number, body: unknown = {}, headers: Record<string, string> = {}) {
  return vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json", ...headers },
    }),
  );
}

async function errorFrom(p: Promise<unknown>): Promise<ApiError> {
  try {
    await p;
  } catch (e) {
    if (e instanceof ApiError) return e;
    throw e;
  }
  throw new Error("expected the request to fail");
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("postJson", () => {
  it("returns the parsed body on success and sends the token", async () => {
    const fetchMock = reply(200, { ok: true });
    vi.stubGlobal("fetch", fetchMock);
    await expect(postJson("/solve", { q: 1 }, "abc")).resolves.toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith(
      "/solve",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer abc" }),
      }),
    );
  });

  it("maps 401 to an auth error", async () => {
    vi.stubGlobal("fetch", reply(401));
    expect((await errorFrom(postJson("/solve", {}, ""))).kind).toBe("auth");
  });

  it("maps 429 to a rate error with the wait time", async () => {
    vi.stubGlobal("fetch", reply(429, {}, { "Retry-After": "12" }));
    const err = await errorFrom(postJson("/solve", {}, "t"));
    expect(err.kind).toBe("rate");
    expect(err.retryAfter).toBe(12);
  });

  it("maps other failures to an http error", async () => {
    vi.stubGlobal("fetch", reply(500));
    expect((await errorFrom(postJson("/solve", {}, "t"))).kind).toBe("http");
  });

  it("maps a failed fetch to a network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    expect((await errorFrom(postJson("/solve", {}, "t"))).kind).toBe("network");
  });

  it("gives up after the timeout", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init: RequestInit) =>
          new Promise((_resolve, reject) => {
            init.signal?.addEventListener("abort", () =>
              reject(new DOMException("Aborted", "AbortError")),
            );
          }),
      ),
    );
    const pending = errorFrom(postJson("/solve", {}, "t", undefined, 1000));
    await vi.advanceTimersByTimeAsync(1000);
    expect((await pending).kind).toBe("timeout");
  });

  it("passes a caller's cancel through as an abort, not an error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init: RequestInit) =>
          new Promise((_resolve, reject) => {
            init.signal?.addEventListener("abort", () =>
              reject(new DOMException("Aborted", "AbortError")),
            );
          }),
      ),
    );
    const caller = new AbortController();
    const pending = postJson("/solve", {}, "t", caller.signal);
    caller.abort();
    await expect(pending).rejects.toMatchObject({ name: "AbortError" });
  });
});
