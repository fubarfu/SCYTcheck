import { CandidateRow, type Candidate } from "./CandidateRow";

export interface CandidateGroup {
  group_id: string;
  display_name: string;
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

  return (
    <section className="candidate-group-card">
      <header className="group-card-header">
        <div className="group-title-stack">
          <h4>{group.display_name}</h4>
          <div className="group-meta-row">
            <span>{group.candidates.length} occurrences</span>
            {typeof group.group_recommendation_score === "number" && (
              <span className="chip recommendation">Group rec {Math.round(group.group_recommendation_score)}</span>
            )}
          </div>
        </div>
        <div className="group-actions">
          <button type="button" className="primary-action" onClick={() => onAction({ action_type: "confirm", target_ids: ids })}>
            Confirm all
          </button>
          <button type="button" className="ghost-action" onClick={() => onAction({ action_type: "reject", target_ids: ids })}>
            Reject all
          </button>
        </div>
      </header>
      <div className="group-candidate-list">
        {group.candidates.map((candidate) => (
          <CandidateRow
            key={candidate.candidate_id}
            candidate={candidate}
            sourceType={sourceType}
            sourceValue={sourceValue}
            onAction={onAction}
            onOpenThumbnail={onOpenThumbnail}
          />
        ))}
      </div>
    </section>
  );
}
