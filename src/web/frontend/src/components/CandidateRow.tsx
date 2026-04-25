import { useEffect, useRef, useState } from "react";

export interface Candidate {
  candidate_id: string;
  extracted_name: string;
  corrected_text?: string;
  start_timestamp?: string;
  status?: "pending" | "confirmed" | "rejected";
}

interface Props {
  candidate: Candidate;
  sourceType: "local_file" | "youtube_url";
  sourceValue: string;
  onAction: (action: {
    action_type: string;
    target_ids: string[];
    payload?: Record<string, unknown>;
  }) => void;
  onOpenThumbnail: (candidateId: string) => void;
  thumbnailUrl?: string | null;
}

function parseTimestampSeconds(raw: string | undefined): number {
  if (!raw) {
    return 0;
  }

  const trimmed = raw.trim();
  const numeric = Number(trimmed);
  if (!Number.isNaN(numeric)) {
    return Math.max(0, Math.floor(numeric));
  }

  if (!trimmed.includes(":")) {
    return 0;
  }

  const parts = trimmed.split(":").map((part) => Number(part));
  if (parts.some((part) => Number.isNaN(part) || part < 0)) {
    return 0;
  }

  let total = 0;
  for (const part of parts) {
    total = (total * 60) + Math.floor(part);
  }
  return Math.max(0, total);
}

function buildYouTubeTimestampLink(sourceValue: string, timestampSeconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(timestampSeconds));
  try {
    const url = new URL(sourceValue);
    url.searchParams.set("t", `${safeSeconds}s`);
    url.searchParams.set("autoplay", "0");
    return url.toString();
  } catch {
    const separator = sourceValue.includes("?") ? "&" : "?";
    return `${sourceValue}${separator}t=${safeSeconds}s&autoplay=0`;
  }
}

export function CandidateRow({
  candidate,
  sourceType,
  sourceValue,
  onAction,
  onOpenThumbnail,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [editedText, setEditedText] = useState(candidate.corrected_text ?? candidate.extracted_name);
  const rowRef = useRef<HTMLDivElement | null>(null);
  const [thumbnailVisible, setThumbnailVisible] = useState(false);

  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") {
      setThumbnailVisible(true);
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          setThumbnailVisible(true);
          observer.disconnect();
          return;
        }
      }
    });
    if (rowRef.current) {
      observer.observe(rowRef.current);
    }
    return () => observer.disconnect();
  }, []);

  const currentText = candidate.corrected_text ?? candidate.extracted_name;
  const timestampSeconds = parseTimestampSeconds(candidate.start_timestamp);
  const deepLink =
    sourceType === "youtube_url" && sourceValue
      ? buildYouTubeTimestampLink(sourceValue, timestampSeconds)
      : null;

  return (
    <div className="candidate-row" ref={rowRef}>
      <div className="candidate-main review-candidate-main">
        <div>
          <strong>{currentText}</strong>
          <div className="candidate-meta-inline">
            <span>{candidate.start_timestamp ?? "-"}</span>
            {deepLink && (
              <a href={deepLink} target="_blank" rel="noreferrer">
                Open at timestamp
              </a>
            )}
          </div>
        </div>
        <span className={`status-chip ${candidate.status ?? "pending"}`}>{candidate.status ?? "pending"}</span>
      </div>
      <div className="candidate-meta">
        <span>Candidate ID: {candidate.candidate_id}</span>
        {candidate.corrected_text && candidate.corrected_text !== candidate.extracted_name && (
          <span>Original OCR: {candidate.extracted_name}</span>
        )}
      </div>

      {editing ? (
        <div className="candidate-edit-row">
          <input
            value={editedText}
            onChange={(e) => setEditedText(e.target.value)}
            placeholder="Corrected player name"
            title="Corrected player name"
          />
          <button
            type="button"
            onClick={() => {
              onAction({
                action_type: "edit",
                target_ids: [candidate.candidate_id],
                payload: { corrected_text: editedText },
              });
              setEditing(false);
            }}
          >
            Save
          </button>
          <button type="button" onClick={() => setEditing(false)}>Cancel</button>
        </div>
      ) : (
        <div className="candidate-actions">
          <button type="button" className="primary-action" onClick={() => onAction({ action_type: "confirm", target_ids: [candidate.candidate_id] })}>Confirm</button>
          <button type="button" className="ghost-action" onClick={() => onAction({ action_type: "reject", target_ids: [candidate.candidate_id] })}>Reject</button>
          <button type="button" className="ghost-action" onClick={() => setEditing(true)}>Edit</button>
          <button type="button" className="ghost-action" onClick={() => onOpenThumbnail(candidate.candidate_id)} disabled={!thumbnailVisible}>Thumbnail</button>
          <button type="button" className="ghost-action" onClick={() => onAction({ action_type: "remove", target_ids: [candidate.candidate_id] })}>Remove</button>
        </div>
      )}
    </div>
  );
}
