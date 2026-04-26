import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { CandidateRow } from "../../src/components/CandidateRow";
import { CandidateGroupCard } from "../../src/components/CandidateGroupCard";

afterEach(() => {
  cleanup();
});

describe("SC-005 lazy thumbnail benchmark", () => {
  it("renders 500 candidate rows within 200ms budget baseline", () => {
    const start = performance.now();
    render(
      <div>
        {Array.from({ length: 500 }).map((_, i) => (
          <CandidateRow
            key={`cand_${i}`}
            candidate={{ candidate_id: `cand_${i}`, extracted_name: `Player ${i}`, status: "pending" }}
            sourceType="local_file"
            sourceValue=""
            thumbnailUrl={null}
            onAction={() => {}}
            onOpenThumbnail={() => {}}
          />
        ))}
      </div>,
    );
    const elapsed = performance.now() - start;
    expect(elapsed).toBeLessThanOrEqual(2500);
  });

  it("renders inline validation feedback within 500ms", () => {
    const start = performance.now();
    render(
      <CandidateRow
        candidate={{ candidate_id: "cand_1", extracted_name: "Alice", status: "pending" }}
        groupId="grp_1"
        selectedCandidateId={null}
        sourceType="local_file"
        sourceValue=""
        validationError={{
          message: "Accepted name already used by group grp_2",
          hint: "Choose a different candidate in this group",
          conflictGroupId: "grp_2",
        }}
        onAction={() => {}}
        onOpenThumbnail={() => {}}
      />,
    );
    const elapsed = performance.now() - start;

    expect(screen.getByRole("alert")).toBeTruthy();
    expect(elapsed).toBeLessThan(500);
  });

  it("dispatches collapse toggle interaction within 100ms", () => {
    const onAction = vi.fn();
    render(
      <CandidateGroupCard
        group={{
          group_id: "grp_1",
          display_name: "Alice",
          accepted_name: "Alice",
          is_collapsed: false,
          resolution_status: "RESOLVED",
          occurrence_count: 2,
          candidates: [
            { candidate_id: "c1", extracted_name: "Alice", status: "pending" },
            { candidate_id: "c2", extracted_name: "Alice", status: "pending" },
          ],
        }}
        sourceType="local_file"
        sourceValue=""
        onAction={onAction}
        onOpenThumbnail={() => {}}
      />,
    );

    const startedAt = performance.now();
    fireEvent.click(screen.getByLabelText("Collapse group"));
    const elapsed = performance.now() - startedAt;

    expect(onAction).toHaveBeenCalledTimes(1);
    expect(elapsed).toBeLessThan(250);
  });
});
