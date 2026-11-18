import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { GuestBanner, GuestLimit } from "./GuestNotices.tsx";

describe("GuestBanner", () => {
  it("before the first answer, doesn't claim a number", () => {
    render(<GuestBanner remaining={null} onLeave={() => {}} />);
    expect(screen.getByRole("status")).toHaveTextContent(/as a guest/);
    expect(screen.getByRole("status")).not.toHaveTextContent(/\d/);
  });

  it("shows what the server said is left, with the right plural", () => {
    const { rerender } = render(<GuestBanner remaining={2} onLeave={() => {}} />);
    expect(screen.getByRole("status")).toHaveTextContent("2 guest problems left.");
    rerender(<GuestBanner remaining={1} onLeave={() => {}} />);
    expect(screen.getByRole("status")).toHaveTextContent("1 guest problem left.");
    rerender(<GuestBanner remaining={0} onLeave={() => {}} />);
    expect(screen.getByRole("status")).toHaveTextContent("That was your last guest problem.");
  });

  it("'Create an account' asks to leave for /signup", () => {
    const onLeave = vi.fn();
    render(<GuestBanner remaining={2} onLeave={onLeave} />);
    fireEvent.click(screen.getByRole("button", { name: "Create an account" }));
    expect(onLeave).toHaveBeenCalledWith("/signup");
  });
});

describe("GuestLimit", () => {
  it("shows the server's message and offers sign-up or sign-in, never a retry", () => {
    const onLeave = vi.fn();
    render(<GuestLimit message="You’ve used all your guest problems." onLeave={onLeave} />);
    expect(screen.getByRole("alert")).toHaveTextContent("You’ve used all your guest problems.");
    expect(screen.queryByRole("button", { name: /try again/i })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(onLeave).toHaveBeenCalledWith("/login");
  });
});