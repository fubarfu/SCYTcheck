import { CandidateRow, type Candidate } from "./CandidateRow";

export interface CandidateGroup {
  group_id: string;
  display_name: string;
  accepted_name?: string | null;
  accepted_name_summary?: string | null;
  is_collapsed?: boolean;
  resolution_status?: string;
  active_spellings?: string[];
  active_candidate_count?: number;
  total_candidate_count?: number;
  occurrence_count?: number;
  is_consensus?: boolean;
  group_recommendation_score?: number;
  candidates: Array<Candidate & { temporal_proximity?: number; recommendation_score?: number }>;
}

interface Props {
  group: CandidateGroup;
  sourceType: "local_file" | "youtube_url";
  sourceValue: string;
  onAction: (action: {
    action_type: string;
    target_ids: string[];
    payload?: Record<string, unknown>;
  }) => void;
  onOpenThumbnail: (candidateId: string) => void;
}

export function CandidateGroupCard({
  group,
  sourceType,
  sourceValue,
  onAction,
  onOpenThumbnail,
}: Props) {
  const ids = group.candidates.map((c) => c.candidate_id);
  const isCollapsed = Boolean(group.is_collapsed);
  const isResolved = (group.resolution_status ?? "UNRESOLVED") === "RESOLVED";
  const activeSpellings = Array.isArray(group.active_spellings) ? group.active_spellings : [];
  const hasConflict = !isResolved && activeSpellings.length > 1;
  const acceptedSummary = group.accepted_name_summary ?? group.accepted_name ?? null;
  const occurrenceCount = group.occurrence_count ?? group.total_candidate_count ?? group.candidates.length;
  const collapseAction = {
    action_type: "toggle_collapse",
    target_ids: [],
    payload: {
      group_id: group.group_id,
      is_collapsed: !isCollapsed,
    },
  };

  return (
    <section
      className={isResolved ? "candidate-group-card group-resolved" : "candidate-group-card group-unresolved"}
      data-testid={`candidate-group-${group.group_id}`}
      data-collapsed={isCollapsed ? "true" : "false"}
      data-resolution={isResolved ? "resolved" : "unresolved"}
    >
      <header className={isResolved ? "group-card-header" : "group-card-header group-card-header-unresolved"}>
        <div className="group-title-stack">
          <h4>{group.display_name}</h4>
          <div className="group-meta-row">
            <span>{occurrenceCount} occurrences</span>
            <span className={isResolved ? "chip recommendation" : "chip"}>{isResolved ? "Resolved" : "Unresolved"}</span>
            {typeof group.group_recommendation_score === "number" && (
              <span className="chip recommendation">Group rec {Math.round(group.group_recommendation_score)}</span>
            )}
          </div>
          {hasConflict && (
            <p className="group-conflict-summary">
              Conflict: {activeSpellings.length} active spellings ({activeSpellings.join(", ")})
            </p>
          )}
          {isResolved && acceptedSummary && (
            <p className="group-accepted-summary">Accepted: <strong>{acceptedSummary}</strong></p>
          )}
        </div>
        <div className="group-actions">
          <button
            type="button"
            className="ghost-action"
            aria-label={isCollapsed ? "Expand group" : "Collapse group"}
            data-testid={`toggle-group-${group.group_id}`}
            onClick={() => onAction(collapseAction)}
          >
            <span aria-hidden="true" className="group-toggle-chevron">{isCollapsed ? ">" : "v"}</span>
            <span>{isCollapsed ? "Expand" : "Collapse"}</span>
          </button>
          {!isCollapsed && (
            <>
              <button type="button" className="primary-action" onClick={() => onAction({ action_type: "confirm", target_ids: ids })}>
                Confirm all
              </button>
              <button type="button" className="ghost-action" onClick={() => onAction({ action_type: "reject", target_ids: ids })}>
                Reject all
              </button>
            </>
          )}
        </div>
      </header>
      {!isCollapsed && (
        <div className="group-candidate-list">
          {group.candidates.map((candidate, index) => (
            <CandidateRow
              key={candidate.candidate_id}
              candidate={candidate}
              sourceType={sourceType}
              sourceValue={sourceValue}
              occurrenceIndex={index + 1}
              occurrenceCount={occurrenceCount}
              showOccurrenceMetadata={isResolved}
              onAction={onAction}
              onOpenThumbnail={onOpenThumbnail}
            />
          ))}
        </div>
      )}
    </section>
  );
}
