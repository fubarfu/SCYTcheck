import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CandidateRow } from "../../src/components/CandidateRow";

afterEach(() => {
  cleanup();
});

describe("CandidateRow feature 010", () => {
  it("dispatches confirm when accept is clicked", () => {
    const onAction = vi.fn();

    render(
      <CandidateRow
        candidate={{ candidate_id: "c1", extracted_name: "Alice", status: "pending" }}
        groupId="grp_1"
        selectedCandidateId={null}
        sourceType="local_file"
        sourceValue=""
        onAction={onAction}
        onOpenThumbnail={() => {}}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Accept" }));

    expect(onAction).toHaveBeenCalledWith({
      action_type: "confirm",
      target_ids: ["c1"],
      payload: { group_id: "grp_1" },
    });
  });

  it("renders accepted state for confirmed candidate", () => {
    render(
      <CandidateRow
        candidate={{ candidate_id: "c1", extracted_name: "Alice", status: "confirmed" }}
        groupId="grp_1"
        selectedCandidateId="c1"
        sourceType="local_file"
        sourceValue=""
        onAction={() => {}}
        onOpenThumbnail={() => {}}
      />,
    );

    expect(screen.getByText("Selection saved")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Accept" })).toBeTruthy();
  });

  it("renders rejected candidate state and dispatches unreject from reject button", () => {
    const onAction = vi.fn();

    render(
      <CandidateRow
        candidate={{ candidate_id: "c2", extracted_name: "Alicia", status: "rejected" }}
        groupId="grp_1"
        selectedCandidateId={null}
        sourceType="local_file"
        sourceValue=""
        onAction={onAction}
        onOpenThumbnail={() => {}}
      />,
    );

    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toContain("Rejected");
    fireEvent.click(screen.getByRole("button", { name: "Reject" }));

    expect(onAction).toHaveBeenCalledWith({
      action_type: "unreject",
      target_ids: ["c2"],
      payload: { group_id: "grp_1" },
    });
  });

  it("renders new badge and dispatches clear_new action", () => {
    const onAction = vi.fn();

    render(
      <CandidateRow
        candidate={{ candidate_id: "c3", extracted_name: "Gamma", status: "pending", marked_new: true }}
        groupId="grp_9"
        selectedCandidateId={null}
        sourceType="local_file"
        sourceValue=""
        onAction={onAction}
        onOpenThumbnail={() => {}}
      />,
    );

    expect(screen.getByText("New")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Clear new marker" }));

    expect(onAction).toHaveBeenCalledWith({
      action_type: "clear_new",
      target_ids: ["c3"],
      payload: { group_id: "grp_9" },
    });
  });
});
