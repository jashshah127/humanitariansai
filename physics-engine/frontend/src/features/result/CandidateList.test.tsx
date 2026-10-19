import { describe, expect, it } from "vitest";
import { render, within } from "@testing-library/react";
import type { Candidate } from "../../api/types.ts";
import { CandidateList } from "./CandidateList.tsx";

const candidates: Candidate[] = [
  { principle: "Kinematics", applies_when: "constant acceleration", answer: { v: 30 } },
  { principle: "Spring energy", applies_when: "a spring is involved", answer: { v: 2.3717 } },
  { principle: "No numbers", applies_when: "anything", answer: null },
];

describe("CandidateList", () => {
  it("shows every candidate, in order, each with its condition and result", () => {
    const { container } = render(<CandidateList candidates={candidates} />);
    const items = container.querySelectorAll("li");
    expect(items).toHaveLength(3);
    expect(items[0]?.textContent).toContain("Use this when: constant acceleration");
    expect(items[0]?.textContent).toContain("v = 30");
    expect(items[1]?.textContent).toContain("Use this when: a spring is involved");
    expect(items[1]?.textContent).toContain("v = 2.3717");
  });

  it("does not print an empty result line for a candidate with no answer", () => {
    const { container } = render(<CandidateList candidates={candidates} />);
    expect(container.querySelectorAll("li")[2]?.textContent).not.toContain("Gives:");
  });

  // Contract: never pick one for the student.
  it("does not mark any candidate as chosen", () => {
    const { container } = render(<CandidateList candidates={candidates} />);
    const view = within(container);
    expect(view.queryByRole("button")).toBeNull();
    expect(
      container.querySelector("[aria-current],[aria-selected='true'],[data-selected]"),
    ).toBeNull();
    expect(container.textContent).not.toMatch(/recommended|best match|most likely/i);
  });
});
