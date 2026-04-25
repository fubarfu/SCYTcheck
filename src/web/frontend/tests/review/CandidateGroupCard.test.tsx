import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CandidateGroupCard } from "../../src/components/CandidateGroupCard";

afterEach(() => {
  cleanup();
});

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
      },
    });
  });
});
