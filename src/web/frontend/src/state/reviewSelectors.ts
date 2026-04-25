import type { Candidate } from "../components/CandidateRow";
import type { CandidateGroup } from "../components/CandidateGroupCard";

export interface ReviewFilterState {
  searchText: string;
  status: "all" | "pending" | "confirmed" | "rejected";
}

export function selectFilteredCandidates(
  candidates: Candidate[],
  filter: ReviewFilterState,
): Candidate[] {
  const search = filter.searchText.trim().toLowerCase();
  return candidates.filter((candidate) => {
    const text = (candidate.corrected_text ?? candidate.extracted_name ?? "").toLowerCase();
    const status = candidate.status ?? "pending";

    if (search && !text.includes(search)) return false;
    if (filter.status !== "all" && status !== filter.status) return false;
    return true;
  });
}

export function selectVisibleCandidateIds(
  candidates: Candidate[],
  filter: ReviewFilterState,
): string[] {
  return selectFilteredCandidates(candidates, filter).map((c) => c.candidate_id);
}

export function selectVisibleGroups(
  groups: CandidateGroup[],
  candidates: Candidate[],
  filter: ReviewFilterState,
): CandidateGroup[] {
  const visibleIds = new Set(selectVisibleCandidateIds(candidates, filter));
  return groups
    .map((group) => ({
      ...group,
      candidates: (group.candidates ?? []).filter((candidate) => visibleIds.has(candidate.candidate_id)),
    }))
    .filter((group) => group.candidates.length > 0);
}

export function isGroupCollapsedByDefault(group: CandidateGroup): boolean {
  const resolved = (group.resolution_status ?? "UNRESOLVED") === "RESOLVED";
  return resolved && Boolean(group.is_collapsed);
}
