import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Input, TextArea } from "./Input.tsx";

describe("Input", () => {
  it("links the label to the input", () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText("Email").tagName).toBe("INPUT");
  });

  it("marks the field invalid and reads out the error", () => {
    render(<Input label="Email" error="Enter an email address." />);
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Enter an email address.");
  });

  it("is not marked invalid without an error", () => {
    render(<Input label="Email" hint="We never share it." />);
    const input = screen.getByLabelText("Email");
    expect(input).not.toHaveAttribute("aria-invalid");
    expect(input).toHaveAccessibleDescription("We never share it.");
  });
});

describe("TextArea", () => {
  it("shows a character count for a controlled value with maxLength", () => {
    render(<TextArea label="Problem" value="abc" maxLength={10} onChange={() => {}} />);
    expect(screen.getByText("3 / 10")).toBeInTheDocument();
  });
});
