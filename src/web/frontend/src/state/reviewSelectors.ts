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
  if (typeof group.is_collapsed === "boolean") {
    return group.is_collapsed;
  }
  if (typeof group.remembered_is_collapsed === "boolean") {
    return group.remembered_is_collapsed;
  }
  return resolved;
}

function normalizeName(value: string | null | undefined): string {
  return String(value ?? "").trim().toLowerCase();
}

export function selectAcceptedCandidateId(group: CandidateGroup): string | null {
  const accepted = normalizeName(group.accepted_name ?? null);
  if (!accepted) {
    return null;
  }
  const match = (group.candidates ?? []).find((candidate) => {
    const candidateName = normalizeName(candidate.corrected_text ?? candidate.extracted_name);
    return candidateName === accepted;
  });
  return match?.candidate_id ?? null;
}

export function selectRejectedCandidateIds(group: CandidateGroup): Set<string> {
  return new Set((group.rejected_candidate_ids ?? []).map((candidateId) => String(candidateId)));
}
