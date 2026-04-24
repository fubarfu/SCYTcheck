import type { Candidate } from "../components/CandidateRow";

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
