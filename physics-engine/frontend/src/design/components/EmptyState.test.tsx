import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmptyState } from "./EmptyState.tsx";

describe("EmptyState", () => {
  it("shows the title at the heading level asked for", () => {
    render(<EmptyState title="No problems yet" headingLevel={1} />);
    expect(screen.getByRole("heading", { level: 1, name: "No problems yet" })).toBeInTheDocument();
  });

  it("defaults to a level-2 heading", () => {
    render(<EmptyState title="No matches" />);
    expect(screen.getByRole("heading", { level: 2, name: "No matches" })).toBeInTheDocument();
  });

  it("shows the body and the next step", () => {
    render(
      <EmptyState title="No matches" action={<button type="button">Clear filters</button>}>
        <p>Try a different topic.</p>
      </EmptyState>,
    );
    expect(screen.getByText("Try a different topic.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Clear filters" })).toBeInTheDocument();
  });
});
