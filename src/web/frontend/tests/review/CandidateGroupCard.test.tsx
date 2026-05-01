import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CandidateGroupCard } from "../../src/components/CandidateGroupCard";

afterEach(() => {
  cleanup();
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

describe("CandidateGroupCard feature 010", () => {
  it("renders resolved groups collapsed by default with accepted-name summary", () => {
    render(
      <CandidateGroupCard
        group={{
          group_id: "grp_1",
          display_name: "Alice",
          accepted_name: "Alice",
          accepted_name_summary: "Alice",
          is_collapsed: true,
          resolution_status: "RESOLVED",
          occurrence_count: 2,
          candidates: [
            { candidate_id: "c1", extracted_name: "Alice #1", status: "pending" },
            { candidate_id: "c2", extracted_name: "Alice #2", status: "pending" },
          ],
        }}
        sourceType="local_file"
        sourceValue=""
        onAction={() => {}}
        onOpenThumbnail={() => {}}
      />,
    );

    expect(screen.getByText("Accepted:")).toBeTruthy();
    expect(screen.getByText("Alice", { selector: "strong" })).toBeTruthy();
    expect(screen.getByLabelText("Expand group")).toBeTruthy();
    expect(screen.queryByText("Alice #1")).toBeNull();
    expect(screen.queryByText("Alice #2")).toBeNull();
  });

  it("dispatches toggle_collapse expand interaction for collapsed groups", () => {
    const onAction = vi.fn();
    render(
      <CandidateGroupCard
        group={{
          group_id: "grp_1",
          display_name: "Alice",
          accepted_name: "Alice",
          is_collapsed: true,
          resolution_status: "RESOLVED",
          occurrence_count: 2,
          candidates: [
            { candidate_id: "c1", extracted_name: "Alice #1", status: "pending" },
            { candidate_id: "c2", extracted_name: "Alice #2", status: "pending" },
          ],
        }}
        sourceType="local_file"
        sourceValue=""
        onAction={onAction}
        onOpenThumbnail={() => {}}
      />,
    );

    fireEvent.click(screen.getByLabelText("Expand group"));

    expect(onAction).toHaveBeenCalledTimes(1);
    expect(onAction).toHaveBeenCalledWith({
      action_type: "toggle_collapse",
      target_ids: [],
      payload: {
        group_id: "grp_1",
        is_collapsed: false,
        resolution_status: "RESOLVED",
      },
    });
  });

  it("renders unresolved groups expanded by default", () => {
    render(
      <CandidateGroupCard
        group={{
          group_id: "grp_conflict",
          display_name: "Alicia",
          accepted_name: null,
          is_collapsed: false,
          resolution_status: "UNRESOLVED",
          active_spellings: ["Alice", "Alicia"],
          occurrence_count: 2,
          candidates: [
            { candidate_id: "c1", extracted_name: "Alice", status: "pending" },
            { candidate_id: "c2", extracted_name: "Alicia", status: "pending" },
          ],
        }}
        sourceType="local_file"
        sourceValue=""
        onAction={() => {}}
        onOpenThumbnail={() => {}}
      />,
    );

    expect(screen.getByText("Unresolved")).toBeTruthy();
    expect(screen.getByLabelText("Collapse group")).toBeTruthy();
    expect(screen.getByText("Alice")).toBeTruthy();
    expect(screen.getAllByText("Alicia").length).toBeGreaterThan(0);
  });

  it("dispatches manual collapse and re-expand actions for unresolved groups", () => {
    const onAction = vi.fn();
    const baseGroup = {
      group_id: "grp_conflict",
      display_name: "Alicia",
      accepted_name: null,
      resolution_status: "UNRESOLVED" as const,
      active_spellings: ["Alice", "Alicia"],
      occurrence_count: 2,
      candidates: [
        { candidate_id: "c1", extracted_name: "Alice", status: "pending" as const },
        { candidate_id: "c2", extracted_name: "Alicia", status: "pending" as const },
      ],
    };

    const { rerender } = render(
      <CandidateGroupCard
        group={{ ...baseGroup, is_collapsed: false }}
        sourceType="local_file"
        sourceValue=""
        onAction={onAction}
        onOpenThumbnail={() => {}}
      />,
    );

    fireEvent.click(screen.getByLabelText("Collapse group"));

    expect(onAction).toHaveBeenCalledWith({
      action_type: "toggle_collapse",
      target_ids: [],
      payload: {
        group_id: "grp_conflict",
        is_collapsed: true,
        resolution_status: "UNRESOLVED",
      },
    });

    rerender(
      <CandidateGroupCard
        group={{ ...baseGroup, is_collapsed: true }}
        sourceType="local_file"
        sourceValue=""
        onAction={onAction}
        onOpenThumbnail={() => {}}
      />,
    );

    fireEvent.click(screen.getByLabelText("Expand group"));

    expect(onAction).toHaveBeenLastCalledWith({
      action_type: "toggle_collapse",
      target_ids: [],
      payload: {
        group_id: "grp_conflict",
        is_collapsed: false,
        resolution_status: "UNRESOLVED",
      },
    });
  });

  it("dispatches manual collapse and re-expand actions for resolved groups", () => {
    const onAction = vi.fn();
    const resolvedGroup = {
      group_id: "grp_resolved",
      display_name: "Alice",
      accepted_name: "Alice",
      accepted_name_summary: "Alice",
      resolution_status: "RESOLVED" as const,
      occurrence_count: 2,
      candidates: [
        { candidate_id: "c1", extracted_name: "Alice #1", status: "pending" as const },
        { candidate_id: "c2", extracted_name: "Alice #2", status: "pending" as const },
      ],
    };

    const { rerender } = render(
      <CandidateGroupCard
        group={{ ...resolvedGroup, is_collapsed: false }}
        sourceType="local_file"
        sourceValue=""
        onAction={onAction}
        onOpenThumbnail={() => {}}
      />,
    );

    fireEvent.click(screen.getByLabelText("Collapse group"));
    expect(onAction).toHaveBeenCalledWith({
      action_type: "toggle_collapse",
      target_ids: [],
      payload: {
        group_id: "grp_resolved",
        is_collapsed: true,
        resolution_status: "RESOLVED",
      },
    });

    rerender(
      <CandidateGroupCard
        group={{ ...resolvedGroup, is_collapsed: true }}
        sourceType="local_file"
        sourceValue=""
        onAction={onAction}
        onOpenThumbnail={() => {}}
      />,
    );

    fireEvent.click(screen.getByLabelText("Expand group"));
    expect(onAction).toHaveBeenLastCalledWith({
      action_type: "toggle_collapse",
      target_ids: [],
      payload: {
        group_id: "grp_resolved",
        is_collapsed: false,
        resolution_status: "RESOLVED",
      },
    });
  });

  it("retains resolved-group toggle controls after reload-hydrated state", () => {
    const onAction = vi.fn();
    render(
      <CandidateGroupCard
        group={{
          group_id: "grp_resolved_hydrated",
          display_name: "Mia",
          accepted_name: "Mia",
          accepted_name_summary: "Mia",
          is_collapsed: true,
          remembered_is_collapsed: true,
          resolution_status: "RESOLVED",
          occurrence_count: 1,
          candidates: [
            { candidate_id: "c1", extracted_name: "Mia", status: "confirmed" },
          ],
        }}
        sourceType="local_file"
        sourceValue=""
        onAction={onAction}
        onOpenThumbnail={() => {}}
      />,
    );

    fireEvent.click(screen.getByLabelText("Expand group"));

    expect(onAction).toHaveBeenCalledWith({
      action_type: "toggle_collapse",
      target_ids: [],
      payload: {
        group_id: "grp_resolved_hydrated",
        is_collapsed: false,
        resolution_status: "RESOLVED",
      },
    });
  });

  it("dispatches merge_groups when a group header is dropped onto another group", () => {
    const onAction = vi.fn();
    const sourceData = createDataTransferMock();

    const { getByTestId, getByText } = render(
      <>
        <CandidateGroupCard
          group={{
            group_id: "grp_source",
            display_name: "Source",
            is_collapsed: false,
            resolution_status: "UNRESOLVED",
            candidates: [{ candidate_id: "c1", extracted_name: "Alice", status: "pending" }],
          }}
          sourceType="local_file"
          sourceValue=""
          onAction={onAction}
          onOpenThumbnail={() => {}}
        />
        <CandidateGroupCard
          group={{
            group_id: "grp_target",
            display_name: "Target",
            is_collapsed: false,
            resolution_status: "UNRESOLVED",
            candidates: [{ candidate_id: "c2", extracted_name: "Alicia", status: "pending" }],
          }}
          sourceType="local_file"
          sourceValue=""
          onAction={onAction}
          onOpenThumbnail={() => {}}
        />
      </>,
    );

    fireEvent.dragStart(screen.getAllByLabelText("Drag group to merge")[0], { dataTransfer: sourceData });
    fireEvent.dragOver(getByTestId("candidate-group-grp_target"), { dataTransfer: sourceData });
    fireEvent.drop(getByTestId("candidate-group-grp_target"), { dataTransfer: sourceData });

    expect(onAction).toHaveBeenCalledWith({
      action_type: "merge_groups",
      target_ids: ["grp_source"],
      payload: {
        source_group_id: "grp_source",
        target_group_id: "grp_target",
        group_id: "grp_target",
      },
    });
  });

  it("dispatches move_candidate when a candidate row is dropped onto another group", () => {
    const onAction = vi.fn();
    const dragData = createDataTransferMock();

    const { getByTestId, getByText } = render(
      <>
        <CandidateGroupCard
          group={{
            group_id: "grp_source",
            display_name: "Source",
            is_collapsed: false,
            resolution_status: "UNRESOLVED",
            candidates: [{ candidate_id: "c1", extracted_name: "Alice", status: "pending" }],
          }}
          sourceType="local_file"
          sourceValue=""
          onAction={onAction}
          onOpenThumbnail={() => {}}
        />
        <CandidateGroupCard
          group={{
            group_id: "grp_target",
            display_name: "Target",
            is_collapsed: false,
            resolution_status: "UNRESOLVED",
            candidates: [{ candidate_id: "c2", extracted_name: "Alicia", status: "pending" }],
          }}
          sourceType="local_file"
          sourceValue=""
          onAction={onAction}
          onOpenThumbnail={() => {}}
        />
      </>,
    );

    fireEvent.dragStart(getByText("Alice").closest(".candidate-row")!, { dataTransfer: dragData });
    fireEvent.dragOver(getByTestId("candidate-group-grp_target"), { dataTransfer: dragData });
    fireEvent.drop(getByTestId("candidate-group-grp_target"), { dataTransfer: dragData });

    expect(onAction).toHaveBeenCalledWith({
      action_type: "move_candidate",
      target_ids: ["c1"],
      payload: {
        candidate_id: "c1",
        source_group_id: "grp_source",
        to_group_id: "grp_target",
        group_id: "grp_target",
      },
    });
  });
});
