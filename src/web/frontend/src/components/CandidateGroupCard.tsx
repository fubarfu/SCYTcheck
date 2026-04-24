import type { Candidate } from "./CandidateRow";

interface Group {
  group_id: string;
  display_name: string;
  candidates: Array<Candidate & { temporal_proximity?: number; recommendation_score?: number }>;
}

interface Props {
  group: Group;
  onBulkConfirm: (ids: string[]) => void;
  onBulkReject: (ids: string[]) => void;
  onReorder: (toIndex: number) => void;
}

export function CandidateGroupCard({ group, onBulkConfirm, onBulkReject, onReorder }: Props) {
  const ids = group.candidates.map((c) => c.candidate_id);
  return (
    <section className="candidate-group-card">
      <header>
        <h4>{group.display_name}</h4>
        <span>{group.candidates.length} candidates</span>
      </header>
      <div className="group-actions">
        <button type="button" onClick={() => onBulkConfirm(ids)}>Bulk confirm</button>
        <button type="button" onClick={() => onBulkReject(ids)}>Bulk reject</button>
        <button type="button" onClick={() => onReorder(0)}>Move to top</button>
      </div>
      <ul>
        {group.candidates.map((candidate) => (
          <li key={candidate.candidate_id} className="group-candidate-row">
            <strong>{candidate.corrected_text ?? candidate.extracted_name}</strong>
            <span className="chip temporal">Temporal {candidate.temporal_proximity ?? 0}</span>
            <span className="chip recommendation">
              Rec {candidate.recommendation_score ?? 0}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
