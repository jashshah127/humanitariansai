import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { VerificationBadge } from "./Badge.tsx";

function stateOf(text: string) {
  return screen.getByText(text).closest("[data-state]")?.getAttribute("data-state");
}

// These tests protect the contract's main rule: nothing is shown as
// "Verified" unless the server said verification === "verified".
describe("VerificationBadge", () => {
  it("shows the server's label for a known state", () => {
    render(<VerificationBadge state="verified" label="Verified by symbolic solver" />);
    expect(stateOf("Verified by symbolic solver")).toBe("verified");
  });

  it("uses a default label when the server sends none", () => {
    render(<VerificationBadge state="needs_review" />);
    expect(stateOf("Needs review")).toBe("needs_review");
  });

  it.each([undefined, null, "", "verfied", "VERIFIED", "approved"])(
    "treats unknown state %j as unverified",
    (state) => {
      render(<VerificationBadge state={state} />);
      expect(stateOf("Unverified")).toBe("unverified");
    },
  );

  it("ignores the server label when the state is unknown", () => {
    render(<VerificationBadge state="verfied" label="Verified" />);
    expect(screen.queryByText("Verified")).toBeNull();
    expect(stateOf("Unverified")).toBe("unverified");
  });

  it("never shows a 'Verified' label on an unverified state", () => {
    render(<VerificationBadge state="unverified" label="Verified" />);
    expect(screen.queryByText("Verified")).toBeNull();
    expect(stateOf("Unverified")).toBe("unverified");
  });

  it("keeps the server label when it doesn't claim verification", () => {
    render(<VerificationBadge state="unverified" label="Unverified - engine error" />);
    expect(stateOf("Unverified - engine error")).toBe("unverified");
  });

  it("hides the icon from screen readers", () => {
    const { container } = render(<VerificationBadge state="verified" />);
    expect(container.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  });
});
