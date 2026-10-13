import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Card } from "./Card.tsx";

describe("Card", () => {
  it("is a named region with a heading when it has a title", () => {
    render(<Card title="Hints">Body</Card>);
    expect(screen.getByRole("region", { name: "Hints" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 3, name: "Hints" })).toBeInTheDocument();
  });

  it("uses the requested heading level", () => {
    render(
      <Card title="Answer" headingLevel={2}>
        Body
      </Card>,
    );
    expect(screen.getByRole("heading", { level: 2, name: "Answer" })).toBeInTheDocument();
  });
});
