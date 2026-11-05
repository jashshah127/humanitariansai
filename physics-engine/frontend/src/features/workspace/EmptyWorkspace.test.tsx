import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmptyWorkspace } from "./EmptyWorkspace.tsx";

describe("EmptyWorkspace", () => {
  it("names the button for the current mode", () => {
    render(<EmptyWorkspace mode="tutor" />);
    expect(screen.getByText(/press “Get hints”/)).toBeInTheDocument();
  });

  it("explains all three labels", () => {
    render(<EmptyWorkspace mode="solve" />);
    for (const label of ["Verified", "Needs review", "Unverified"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });
});
