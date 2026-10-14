import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { VerificationBadge } from "./Badge.tsx";

function badgeText(state: string | null | undefined, label?: string | null) {
  const { container } = render(<VerificationBadge state={state} label={label} />);
  return container.querySelector("[data-state]")?.textContent ?? "";
}

describe("VerificationBadge label rule", () => {
  it("keeps the server's real labels", () => {
    expect(badgeText("verified", "Verified - solved symbolically")).toBe(
      "Verified - solved symbolically",
    );
    expect(badgeText("needs_review", "Needs review - more than one principle applies")).toBe(
      "Needs review - more than one principle applies",
    );
    expect(badgeText("unverified", "Unverified - engine error")).toBe("Unverified - engine error");
  });

  it("never shows a 'verified' label on a state that isn't verified", () => {
    expect(badgeText("needs_review", "✓ Verified")).toBe("Needs review");
    expect(badgeText("needs_review", "Symbolically verified")).toBe("Needs review");
    expect(badgeText("unverified", "Verified - solved symbolically")).toBe("Unverified");
  });

  it("treats an unknown state as unverified, whatever the label says", () => {
    expect(badgeText("VERIFIED", "Verified - solved symbolically")).toBe("Unverified");
    expect(badgeText(undefined, "Verified")).toBe("Unverified");
  });

  it("rejects labels that only look like the state name", () => {
    expect(badgeText("verified", "Verifiedish")).toBe("Verified");
  });
});
