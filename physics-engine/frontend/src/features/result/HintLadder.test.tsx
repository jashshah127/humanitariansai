import { describe, expect, it } from "vitest";
import { fireEvent, render, within } from "@testing-library/react";
import { HintLadder } from "./HintLadder.tsx";

describe("HintLadder", () => {
  it("reveals one hint at a time and names the last step", () => {
    const { container } = render(<HintLadder hints={["first", "second", "answer"]} />);
    const view = within(container);

    expect(container.querySelectorAll("li")).toHaveLength(1);

    fireEvent.click(view.getByRole("button", { name: "Show next hint" }));
    expect(container.querySelectorAll("li")).toHaveLength(2);

    fireEvent.click(view.getByRole("button", { name: "Show the answer" }));
    expect(container.querySelectorAll("li")).toHaveLength(3);
    expect(view.queryByRole("button")).toBeNull();
  });
});
