import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { CandidateRow } from "../../src/components/CandidateRow";

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
    expect(elapsed).toBeLessThanOrEqual(200);
  });
});
