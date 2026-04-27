import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GroupListItem } from "../../src/components/GroupListItem";
import { resetDragSession } from "../../src/state/dragPayload";

afterEach(() => {
  cleanup();
  resetDragSession();
});

function createDataTransferMock() {
  const data = new Map<string, string>();
  return {
    data,
    dropEffect: "move",
    effectAllowed: "all",
    types: [] as string[],
    setData(type: string, value: string) {
      data.set(type, value);
      this.types = Array.from(data.keys());
    },
    getData(type: string) {
      return data.get(type) ?? "";
    },
  };
}

describe("GroupListItem drag and drop", () => {
  it("dispatches merge callback when a different group is dropped onto the rail item", () => {
    const onMergeGroups = vi.fn();
    const onMoveCandidate = vi.fn();
    const dragData = createDataTransferMock();
    dragData.setData("application/x-scyt-group-id", "grp_source");
    dragData.setData("text/plain", JSON.stringify({ kind: "group", group_id: "grp_source" }));

    render(
      <GroupListItem
        group={{
          group_id: "grp_target",
          display_name: "Target",
          resolution_status: "UNRESOLVED",
          candidates: [{ candidate_id: "c1", extracted_name: "Alice", status: "pending" }],
        }}
        isSelected={false}
        onSelect={() => {}}
        onMergeGroups={onMergeGroups}
        onMoveCandidate={onMoveCandidate}
      />,
    );

    const railItem = screen.getByTestId("group-rail-item-grp_target");
    fireEvent.dragOver(railItem, { dataTransfer: dragData });
    fireEvent.drop(railItem, { dataTransfer: dragData });

    expect(onMergeGroups).toHaveBeenCalledTimes(1);
    expect(onMergeGroups).toHaveBeenCalledWith("grp_source", "grp_target");
  });

  it("ignores drops where source and target group are the same", () => {
    const onMergeGroups = vi.fn();
    const onMoveCandidate = vi.fn();
    const dragData = createDataTransferMock();
    dragData.setData("application/x-scyt-group-id", "grp_target");

    render(
      <GroupListItem
        group={{
          group_id: "grp_target",
          display_name: "Target",
          resolution_status: "RESOLVED",
          candidates: [{ candidate_id: "c1", extracted_name: "Alice", status: "confirmed" }],
        }}
        isSelected={true}
        onSelect={() => {}}
        onMergeGroups={onMergeGroups}
        onMoveCandidate={onMoveCandidate}
      />,
    );

    const railItem = screen.getByTestId("group-rail-item-grp_target");
    fireEvent.dragOver(railItem, { dataTransfer: dragData });
    fireEvent.drop(railItem, { dataTransfer: dragData });

    expect(onMergeGroups).not.toHaveBeenCalled();
  });

  it("dispatches move callback when a candidate is dropped onto the rail item", () => {
    const onMergeGroups = vi.fn();
    const onMoveCandidate = vi.fn();
    const dragData = createDataTransferMock();
    dragData.setData(
      "application/x-scyt-candidate",
      JSON.stringify({ kind: "candidate", candidate_id: "cand_1", source_group_id: "grp_source" }),
    );
    dragData.setData(
      "text/plain",
      JSON.stringify({ kind: "candidate", candidate_id: "cand_1", source_group_id: "grp_source" }),
    );

    render(
      <GroupListItem
        group={{
          group_id: "grp_target",
          display_name: "Target",
          resolution_status: "UNRESOLVED",
          candidates: [{ candidate_id: "c1", extracted_name: "Alice", status: "pending" }],
        }}
        isSelected={false}
        onSelect={() => {}}
        onMergeGroups={onMergeGroups}
        onMoveCandidate={onMoveCandidate}
      />,
    );

    const railItem = screen.getByTestId("group-rail-item-grp_target");
    fireEvent.dragOver(railItem, { dataTransfer: dragData });
    fireEvent.drop(railItem, { dataTransfer: dragData });

    expect(onMergeGroups).not.toHaveBeenCalled();
    expect(onMoveCandidate).toHaveBeenCalledTimes(1);
    expect(onMoveCandidate).toHaveBeenCalledWith("cand_1", "grp_source", "grp_target");
  });
});
