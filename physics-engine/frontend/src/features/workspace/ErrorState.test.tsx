import { afterEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, within } from "@testing-library/react";
import { ApiError } from "../../api/client.ts";
import { ErrorState } from "./ErrorState.tsx";

afterEach(() => vi.useRealTimers());

describe("ErrorState", () => {
  it("offers a retry for network errors", () => {
    const onRetry = vi.fn();
    const { container } = render(
      <ErrorState error={new ApiError("network", "Can't reach the server.")} onRetry={onRetry} />,
    );
    fireEvent.click(within(container).getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("does not offer a retry for auth errors", () => {
    const { container } = render(
      <ErrorState error={new ApiError("auth", "Bad token.")} onRetry={() => {}} />,
    );
    expect(within(container).queryByRole("button")).toBeNull();
  });

  it("keeps retry disabled until the rate-limit wait is over", () => {
    vi.useFakeTimers();
    const { container } = render(
      <ErrorState error={new ApiError("rate", "Too many requests.", 2)} onRetry={() => {}} />,
    );
    const button = within(container).getByRole("button", { name: "Try again" });
    expect(button).toHaveProperty("disabled", true);
    act(() => vi.advanceTimersByTime(1000));
    act(() => vi.advanceTimersByTime(1000));
    expect(button).toHaveProperty("disabled", false);
  });
});
