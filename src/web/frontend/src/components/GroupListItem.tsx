import type { CandidateGroup } from "./CandidateGroupCard";

interface Props {
  group: CandidateGroup;
  isSelected: boolean;
  hasValidationError?: boolean;
  onSelect: (groupId: string) => void;
}

/**
 * Compact entry shown in the left "groups rail" of the review workspace.
 * Mirrors the Stitch designs: status pill (Resolved / In Review / Conflict) plus
 * a count of matched candidates.
 */
export function GroupListItem({ group, isSelected, hasValidationError = false, onSelect }: Props) {
  const isResolved = (group.resolution_status ?? "UNRESOLVED") === "RESOLVED";
  const activeSpellings = Array.isArray(group.active_spellings) ? group.active_spellings : [];
  const hasConflict = !isResolved && activeSpellings.length > 1;
  const hasIssue = !isResolved;
  const candidateCount = group.total_candidate_count ?? group.candidates.length;
  const occurrenceCount = group.occurrence_count ?? candidateCount;
  const acceptedSummary = group.accepted_name_summary ?? group.accepted_name ?? null;

  let statusLabel = "Unresolved";
  let statusVariant = "status-pending";
  if (hasValidationError) {
    statusLabel = "Conflict";
    statusVariant = "status-error";
  } else if (hasIssue) {
    statusLabel = hasConflict ? "In Review" : "Unresolved";
    statusVariant = "status-error";
  } else if (isResolved) {
    statusLabel = "Resolved";
    statusVariant = "status-resolved";
  }

  const subtitle = isResolved && acceptedSummary
    ? acceptedSummary
    : `${candidateCount} candidate${candidateCount === 1 ? "" : "s"} matched`;

  return (
    <button
      type="button"
      className={`group-rail-item${isSelected ? " is-selected" : ""}${hasValidationError || hasIssue ? " has-issue" : ""}`}
      data-testid={`group-rail-item-${group.group_id}`}
      data-status={statusVariant}
      data-selected={isSelected ? "true" : "false"}
      onClick={() => onSelect(group.group_id)}
    >
      <div className="group-rail-heading">
        {(hasValidationError || hasIssue) && (
          <span className="group-rail-issue-icon material-symbols-outlined" aria-hidden="true">warning</span>
        )}
        <span className="group-rail-title">{group.display_name}</span>
        <span className={`group-rail-status ${statusVariant}`}>{statusLabel}</span>
      </div>
      <div className="group-rail-meta">
        <span>{subtitle}</span>
        <span className="group-rail-count">{occurrenceCount} occ.</span>
      </div>
    </button>
  );
}
