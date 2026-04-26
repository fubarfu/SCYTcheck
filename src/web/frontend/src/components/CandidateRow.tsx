import { useEffect, useRef, useState } from "react";
import { ValidationFeedback } from "./ValidationFeedback";
import {
  getDropCommitted,
  getHoveredGroupId,
  getHoveredNewGroupZone,
  resetDragSession,
  setDropCommitted,
  setDraggedCandidate,
  setDraggedGroupId,
} from "../state/dragPayload";

const CANDIDATE_DRAG_MIME = "application/x-scyt-candidate";
const FALLBACK_DRAG_MIME = "text/plain";

export interface Candidate {
  candidate_id: string;
  extracted_name: string;
  corrected_text?: string;
  start_timestamp?: string;
  status?: "pending" | "confirmed" | "rejected";
  temporal_proximity?: number;
  recommendation_score?: number;
  recommendation?: "auto_confirm" | "review";
}

interface Props {
  candidate: Candidate;
  groupId?: string;
  selectedCandidateId?: string | null;
  sourceType: "local_file" | "youtube_url";
  sourceValue: string;
  occurrenceIndex?: number;
  occurrenceCount?: number;
  showOccurrenceMetadata?: boolean;
  onAction: (action: {
    action_type: string;
    target_ids: string[];
    payload?: Record<string, unknown>;
  }) => void;
  onOpenThumbnail: (candidateId: string) => void;
  thumbnailUrl?: string | null;
  validationError?: {
    message: string;
    hint?: string | null;
    conflictGroupId?: string | null;
  } | null;
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
  groupId,
  selectedCandidateId = null,
  sourceType,
  sourceValue,
  occurrenceIndex,
  occurrenceCount,
  showOccurrenceMetadata = false,
  onAction,
  onOpenThumbnail,
  validationError = null,
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
  const currentStatus = candidate.status ?? "pending";
  const isSelected = selectedCandidateId === candidate.candidate_id || currentStatus === "confirmed";
  const isRejected = currentStatus === "rejected";
  const timestampSeconds = parseTimestampSeconds(candidate.start_timestamp);
  const deepLink =
    sourceType === "youtube_url" && sourceValue
      ? buildYouTubeTimestampLink(sourceValue, timestampSeconds)
      : null;

  return (
    <div
      className="candidate-row"
      ref={rowRef}
      draggable
      onDragStart={(event) => {
        event.stopPropagation();
        if (typeof event.dataTransfer.clearData === "function") {
          event.dataTransfer.clearData();
        }
        const payload = JSON.stringify({
          kind: "candidate",
          candidate_id: candidate.candidate_id,
          source_group_id: groupId ?? null,
        });
        event.dataTransfer.setData(CANDIDATE_DRAG_MIME, payload);
        event.dataTransfer.setData(FALLBACK_DRAG_MIME, payload);
        event.dataTransfer.effectAllowed = "move";
        setDropCommitted(false);
        setDraggedGroupId(null);
        setDraggedCandidate({
          candidate_id: candidate.candidate_id,
          source_group_id: groupId ?? null,
        });
      }}
      onDragEnd={() => {
        const didCommit = getDropCommitted();
        const hoveredGroupId = getHoveredGroupId();
        const hoveredNewGroup = getHoveredNewGroupZone();

        if (!didCommit && hoveredGroupId && hoveredGroupId !== (groupId ?? null)) {
          onAction({
            action_type: "move_candidate",
            target_ids: [candidate.candidate_id],
            payload: {
              candidate_id: candidate.candidate_id,
              source_group_id: groupId ?? null,
              to_group_id: hoveredGroupId,
              group_id: hoveredGroupId,
            },
          });
        } else if (!didCommit && hoveredNewGroup) {
          onAction({
            action_type: "move_candidate",
            target_ids: [candidate.candidate_id],
            payload: {
              candidate_id: candidate.candidate_id,
              source_group_id: groupId ?? null,
              create_new_group: true,
            },
          });
        }

        resetDragSession();
      }}
    >
      <div className="candidate-main review-candidate-main">
        <div>
          <div className="candidate-radio-row">
            <strong>{currentText}</strong>
          </div>
          <div className="candidate-meta-inline">
            <span>{candidate.start_timestamp ?? "-"}</span>
            {typeof candidate.recommendation_score === "number" && (
              <span className="chip recommendation">Rec {Math.round(candidate.recommendation_score)}</span>
            )}
            {deepLink && (
              <a href={deepLink} target="_blank" rel="noreferrer">
                Open at timestamp
              </a>
            )}
          </div>
        </div>
        <span className={`status-chip ${currentStatus}`}>{currentStatus.charAt(0).toUpperCase()}{currentStatus.slice(1)}</span>
      </div>
      <div className="candidate-meta">
        <span>Candidate ID: {candidate.candidate_id}</span>
        {showOccurrenceMetadata && typeof occurrenceIndex === "number" && typeof occurrenceCount === "number" && (
          <span>Occurrence {occurrenceIndex} of {occurrenceCount}</span>
        )}
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
          <div className="candidate-decision-actions" role="group" aria-label="Decision actions">
            <button
              type="button"
              className={`decision-action${isSelected ? " is-selected" : ""}`}
              onClick={() => onAction({
                action_type: "confirm",
                target_ids: [candidate.candidate_id],
                payload: groupId ? { group_id: groupId } : undefined,
              })}
            >
              Accept
            </button>
            <button
              type="button"
              className={`decision-action${isRejected ? " is-selected" : ""}`}
              onClick={() => onAction({
                action_type: isRejected ? "unreject" : "reject",
                target_ids: [candidate.candidate_id],
                payload: groupId ? { group_id: groupId } : undefined,
              })}
            >
              Reject
            </button>
          </div>
          <div className="candidate-secondary-actions" role="group" aria-label="Candidate tools">
            <button
              type="button"
              className="ghost-action icon-tool-button"
              aria-label="Open thumbnail"
              title="Open thumbnail"
              onClick={() => onOpenThumbnail(candidate.candidate_id)}
              disabled={!thumbnailVisible}
            >
              <span className="material-symbols-outlined" aria-hidden="true">image</span>
            </button>
            <button
              type="button"
              className="ghost-action icon-tool-button"
              aria-label="Edit candidate"
              title="Edit candidate"
              onClick={() => setEditing(true)}
            >
              <span className="material-symbols-outlined" aria-hidden="true">edit</span>
            </button>
            <button
              type="button"
              className="ghost-action icon-tool-button"
              aria-label="Remove candidate"
              title="Remove candidate"
              onClick={() => onAction({ action_type: "remove", target_ids: [candidate.candidate_id] })}
            >
              <span className="material-symbols-outlined" aria-hidden="true">delete</span>
            </button>
          </div>
        </div>
      )}

      {isSelected && (
        <ValidationFeedback
          type="success"
          message="Selection saved"
          hint="This candidate is now the accepted name for the group."
        />
      )}
      {validationError && (
        <ValidationFeedback
          type="error"
          message={validationError.message}
          hint={validationError.hint}
          conflictGroupId={validationError.conflictGroupId}
        />
      )}
      {isRejected && <ValidationFeedback type="error" message="Rejected" hint="This candidate is excluded until you undo reject." />}
    </div>
  );
}
