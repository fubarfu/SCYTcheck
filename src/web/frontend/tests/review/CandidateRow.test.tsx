import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CandidateRow } from "../../src/components/CandidateRow";

afterEach(() => {
  cleanup();
});

describe("CandidateRow feature 010", () => {
  it("dispatches confirm when radio selection changes", () => {
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

    fireEvent.click(screen.getByLabelText("Select candidate Alice"));

    expect(onAction).toHaveBeenCalledWith({
      action_type: "confirm",
      target_ids: ["c1"],
      payload: { group_id: "grp_1" },
    });
  });

  it("dispatches deselect for the selected candidate and renders success feedback", () => {
    const onAction = vi.fn();

    render(
      <CandidateRow
        candidate={{ candidate_id: "c1", extracted_name: "Alice", status: "confirmed" }}
        groupId="grp_1"
        selectedCandidateId="c1"
        sourceType="local_file"
        sourceValue=""
        onAction={onAction}
        onOpenThumbnail={() => {}}
      />,
    );

    expect(screen.getByText("Selection saved")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Clear selection" }));

    expect(onAction).toHaveBeenCalledWith({
      action_type: "deselect",
      target_ids: [],
      payload: { group_id: "grp_1" },
    });
  });

  it("renders rejected candidate state and dispatches unreject", () => {
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
    fireEvent.click(screen.getByRole("button", { name: "Undo reject" }));

    expect(onAction).toHaveBeenCalledWith({
      action_type: "unreject",
      target_ids: ["c2"],
      payload: { group_id: "grp_1" },
    });
  });
});
