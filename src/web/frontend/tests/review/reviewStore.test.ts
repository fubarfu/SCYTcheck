import { describe, expect, it } from "vitest";

import {
  applyGroupToggleState,
  deriveGroupToggleState,
  reconcileGroupMutationState,
  updateGroupToggleState,
} from "../../src/state/reviewStore";

describe("reviewStore feature 010", () => {
  it("derives and applies mixed toggle states for resolved and unresolved groups", () => {
    const groups = [
      {
        group_id: "grp_resolved",
        resolution_status: "RESOLVED",
        is_collapsed: false,
      },
      {
        group_id: "grp_unresolved",
        resolution_status: "UNRESOLVED",
        is_collapsed: true,
      },
    ];

    const toggles = deriveGroupToggleState(groups);
    expect(toggles).toEqual({ grp_resolved: false, grp_unresolved: true });

    const session = {
      groups: [
        { ...groups[0], is_collapsed: true },
        { ...groups[1], is_collapsed: false },
      ],
    };
    const hydrated = applyGroupToggleState(session, toggles);
    expect(hydrated.groups?.map((group) => group.is_collapsed)).toEqual([false, true]);
  });

  it("keeps manual expansion for resolved groups during mutation reconciliation", () => {
    const reconciled = reconcileGroupMutationState({
      groups: [
        {
          group_id: "grp_1",
          accepted_name: "Alice",
          resolution_status: "RESOLVED",
          is_collapsed: false,
          rejected_candidate_ids: [],
          candidates: [
            { candidate_id: "c1", extracted_name: "Alice" },
            { candidate_id: "c2", extracted_name: "Alice" },
          ],
        },
      ],
    });

    const group = reconciled.groups?.[0];
    expect(group?.resolution_status).toBe("RESOLVED");
    expect(group?.is_collapsed).toBe(false);
    expect(group?.candidates?.map((candidate) => candidate.status)).toEqual(["confirmed", "confirmed"]);
  });

  it("updates one toggle entry without mutating existing group toggle map", () => {
    const initial = {
      grp_1: false,
      grp_2: true,
    };

    const next = updateGroupToggleState(initial, "grp_1", true);
    expect(initial).toEqual({ grp_1: false, grp_2: true });
    expect(next).toEqual({ grp_1: true, grp_2: true });
  });

  it("hydrates toggle state from remembered_is_collapsed when is_collapsed is missing", () => {
    const toggles = deriveGroupToggleState([
      {
        group_id: "grp_1",
        resolution_status: "RESOLVED",
        remembered_is_collapsed: false,
      },
    ]);

    expect(toggles).toEqual({ grp_1: false });

    const reconciled = reconcileGroupMutationState({
      groups: [
        {
          group_id: "grp_1",
          accepted_name: "Alice",
          resolution_status: "RESOLVED",
          remembered_is_collapsed: false,
          candidates: [{ candidate_id: "c1", extracted_name: "Alice" }],
        },
      ],
    });
    expect(reconciled.groups?.[0]?.is_collapsed).toBe(false);
  });

  it("preserves mixed collapse states after confirm/reject-style reconciliation and reload hydration", () => {
    const hydrated = {
      groups: [
        {
          group_id: "grp_resolved",
          accepted_name: "Alice",
          resolution_status: "RESOLVED",
          remembered_is_collapsed: false,
          candidates: [
            { candidate_id: "c1", extracted_name: "Alice" },
            { candidate_id: "c2", extracted_name: "Alice" },
          ],
        },
        {
          group_id: "grp_unresolved",
          accepted_name: null,
          resolution_status: "UNRESOLVED",
          remembered_is_collapsed: true,
          rejected_candidate_ids: ["c4"],
          candidates: [
            { candidate_id: "c3", extracted_name: "Alicia" },
            { candidate_id: "c4", extracted_name: "Alice" },
          ],
        },
      ],
    };

    const reconciled = reconcileGroupMutationState(hydrated);
    const toggles = deriveGroupToggleState(reconciled.groups ?? []);
    const applied = applyGroupToggleState(reconciled, toggles);
    expect(applied.groups?.map((group) => group.is_collapsed)).toEqual([false, true]);
  });
});
