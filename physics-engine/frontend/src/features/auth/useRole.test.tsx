import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useRole } from "./useRole.ts";

const fetchMock = vi.fn();

function reply(status: number, body: unknown): Promise<Response> {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

const asUser = () => reply(200, { kind: "supabase", id: "u1", email: "a@test.dev", role: "user" });
const asAdmin = () =>
  reply(200, { kind: "supabase", id: "u1", email: "a@test.dev", role: "admin" });

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => vi.unstubAllGlobals());

describe("useRole", () => {
  it("makes no call while signed out", () => {
    const { result } = renderHook(() => useRole(null, ""));
    expect(result.current).toEqual({ role: null, roleStatus: "idle" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("reads a normal user's role with a GET to /me", async () => {
    fetchMock.mockImplementation(asUser);
    const { result } = renderHook(() => useRole("u1", "t1"));
    expect(result.current.roleStatus).toBe("loading");
    await waitFor(() => expect(result.current.roleStatus).toBe("ready"));
    expect(result.current.role).toBe("user");

    expect(fetchMock).toHaveBeenCalledWith(
      "/me",
      expect.objectContaining({
        method: "GET",
        headers: { Authorization: "Bearer t1" },
        body: undefined,
      }),
    );
  });

  it("reads an admin's role", async () => {
    fetchMock.mockImplementation(asAdmin);
    const { result } = renderHook(() => useRole("u1", "t1"));
    await waitFor(() => expect(result.current.role).toBe("admin"));
  });

  it("treats a minted token (no role) as not an admin", async () => {
    fetchMock.mockImplementation(() => reply(200, { kind: "minted", sub: "dev", role: null }));
    const { result } = renderHook(() => useRole("u1", "t1"));
    await waitFor(() => expect(result.current.roleStatus).toBe("ready"));
    expect(result.current.role).toBe("user");
  });

  it.each([
    ["a refused token (401)", () => reply(401, { error: "unauthorized" })],
    ["Supabase being down (503)", () => reply(503, { error: "Your role can't be checked" })],
    ["no network", () => Promise.reject(new TypeError("Failed to fetch"))],
  ])("fails closed on %s: no role, not an admin", async (_name, impl) => {
    fetchMock.mockImplementation(impl);
    const { result } = renderHook(() => useRole("u1", "t1"));
    await waitFor(() => expect(result.current.roleStatus).toBe("failed"));
    expect(result.current.role).toBeNull();
  });

  it("does not ask again when the token refreshes for the same user", async () => {
    fetchMock.mockImplementation(asAdmin);
    const { result, rerender } = renderHook(({ id, tok }) => useRole(id, tok), {
      initialProps: { id: "u1", tok: "t1" },
    });
    await waitFor(() => expect(result.current.role).toBe("admin"));
    rerender({ id: "u1", tok: "t2" });
    expect(result.current.role).toBe("admin");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("asks again for a different user", async () => {
    fetchMock.mockImplementationOnce(asAdmin).mockImplementationOnce(asUser);
    const { result, rerender } = renderHook(({ id, tok }) => useRole(id, tok), {
      initialProps: { id: "u1", tok: "t1" },
    });
    await waitFor(() => expect(result.current.role).toBe("admin"));
    rerender({ id: "u2", tok: "t9" });
    expect(result.current.roleStatus).toBe("loading"); // never shows u1's role to u2
    await waitFor(() => expect(result.current.role).toBe("user"));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("asks again after signing out and back in (the role may have changed)", async () => {
    fetchMock.mockImplementationOnce(asUser).mockImplementationOnce(asAdmin);
    const { result, rerender } = renderHook(({ id, tok }) => useRole(id, tok), {
      initialProps: { id: "u1" as string | null, tok: "t1" },
    });
    await waitFor(() => expect(result.current.role).toBe("user"));
    rerender({ id: null, tok: "" });
    expect(result.current.roleStatus).toBe("idle");
    rerender({ id: "u1", tok: "t2" });
    await waitFor(() => expect(result.current.role).toBe("admin"));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
