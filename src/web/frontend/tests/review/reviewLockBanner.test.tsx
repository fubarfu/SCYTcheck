import { describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach } from "vitest";
import { ReviewLockBanner } from "../../src/components/ReviewLockBanner";

afterEach(() => {
  cleanup();
});

describe("ReviewLockBanner (feature 012)", () => {
  it("renders nothing when readonly is false", () => {
    const { container } = render(
      <ReviewLockBanner readonly={false} ownerSessionId={null} currentSessionId={null} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders alert region when readonly is true", () => {
    render(
      <ReviewLockBanner readonly={true} ownerSessionId={null} currentSessionId={null} />,
    );
    expect(screen.getByRole("alert")).toBeTruthy();
  });

  it("mentions 'another session' when ownerSessionId is null", () => {
    render(
      <ReviewLockBanner readonly={true} ownerSessionId={null} currentSessionId={null} />,
    );
    expect(screen.getByRole("alert").textContent).toContain("another session");
  });

  it("shows a truncated owner session ID label when ownerSessionId is provided", () => {
    render(
      <ReviewLockBanner
        readonly={true}
        ownerSessionId="abc12345-0000-0000-0000-000000000000"
        currentSessionId={null}
      />,
    );
    expect(screen.getByRole("alert").textContent).toContain("Session abc12345");
  });

  it("mentions the current session ID when currentSessionId is provided", () => {
    render(
      <ReviewLockBanner
        readonly={true}
        ownerSessionId="abc12345-0000-0000-0000-000000000000"
        currentSessionId="cur56789-0000-0000-0000-000000000000"
      />,
    );
    expect(screen.getByRole("alert").textContent).toContain("cur56789");
  });
});
