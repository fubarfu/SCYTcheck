import { useEffect, useRef, useState, useCallback, memo, useMemo } from "react";
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
  marked_new?: boolean;
  temporal_proximity?: number;
  recommendation_score?: number;
  recommendation?: "auto_confirm" | "review";
  validation_state?: "unchecked" | "checking" | "found" | "not_found" | "failed";
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
  thumbnailCheckUrl?: string | null;
  onRecheck?: (candidateId: string, spelling: string) => void;
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
    const normalized = numeric >= 10000 ? numeric / 1000 : numeric;
    return Math.max(0, Math.floor(normalized));
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

function buildRsiCitizenLink(spelling: string): string {
  const safeName = encodeURIComponent(spelling.trim());
  return `https://robertsspaceindustries.com/en/citizens/${safeName}`;
}

function CandidateRowComponent({
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
  onRecheck,
  validationError = null,
  thumbnailCheckUrl,
}: Props & { thumbnailCheckUrl?: string | null }) {
  const [editing, setEditing] = useState(false);
  const [editedText, setEditedText] = useState(candidate.corrected_text ?? candidate.extracted_name);
  const rowRef = useRef<HTMLDivElement | null>(null);
  const [thumbnailVisible, setThumbnailVisible] = useState(false);
  const [resolvedThumbnailSrc, setResolvedThumbnailSrc] = useState<string | null>(null);

  useEffect(() => {
    if (typeof IntersectionObserver === "undefined" || typeof window === "undefined") {
      setThumbnailVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setThumbnailVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0 }
    );
    if (rowRef.current) {
      observer.observe(rowRef.current);
    }
    return () => { observer.disconnect(); };
  }, []);

  useEffect(() => {
    if (!thumbnailVisible || !thumbnailCheckUrl) return;
    let cancelled = false;
    fetch(thumbnailCheckUrl)
      .then(async (resp) => {
        if (!resp.ok || cancelled) return;
        const body = await resp.json() as { thumbnail_url?: string };
        if (body.thumbnail_url && !cancelled) {
          setResolvedThumbnailSrc(body.thumbnail_url);
        }
      })
      .catch(() => { /* no thumbnail available */ });
    return () => { cancelled = true; };
  }, [thumbnailVisible, thumbnailCheckUrl]);

  const currentText = candidate.corrected_text ?? candidate.extracted_name;
  const currentStatus = candidate.status ?? "pending";
  const isSelected = selectedCandidateId === candidate.candidate_id || currentStatus === "confirmed";
  const isRejected = currentStatus === "rejected";
  
  const { timestampSeconds, deepLink } = useMemo(() => {
    const seconds = parseTimestampSeconds(candidate.start_timestamp);
    const link =
      sourceType === "youtube_url" && sourceValue
        ? buildYouTubeTimestampLink(sourceValue, seconds)
        : null;
    return { timestampSeconds: seconds, deepLink: link };
  }, [candidate.start_timestamp, sourceType, sourceValue]);

  const handleDragStart = useCallback((event: React.DragEvent<HTMLDivElement>) => {
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
  }, [candidate.candidate_id, groupId]);

  const handleDragEnd = useCallback(() => {
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
  }, [onAction, candidate.candidate_id, groupId]);

  const handleConfirm = useCallback(() => {
    onAction({
      action_type: "confirm",
      target_ids: [candidate.candidate_id],
      payload: groupId ? { group_id: groupId } : undefined,
    });
  }, [onAction, candidate.candidate_id, groupId]);

  const handleReject = useCallback(() => {
    onAction({
      action_type: isRejected ? "unreject" : "reject",
      target_ids: [candidate.candidate_id],
      payload: groupId ? { group_id: groupId } : undefined,
    });
  }, [onAction, candidate.candidate_id, isRejected, groupId]);

  const handleOpenThumbnail = useCallback(() => {
    onOpenThumbnail(candidate.candidate_id);
  }, [onOpenThumbnail, candidate.candidate_id]);

  const handleEdit = useCallback(() => {
    setEditing(true);
  }, []);

  const handleSaveEdit = useCallback(() => {
    onAction({
      action_type: "edit",
      target_ids: [candidate.candidate_id],
      payload: { corrected_text: editedText },
    });
    setEditing(false);
  }, [onAction, candidate.candidate_id, editedText]);

  const handleRemove = useCallback(() => {
    onAction({ action_type: "remove", target_ids: [candidate.candidate_id] });
  }, [onAction, candidate.candidate_id]);

  const handleOpenRsiProfile = useCallback(() => {
    const spelling = (candidate.corrected_text ?? candidate.extracted_name).trim();
    if (!spelling) {
      return;
    }
    const url = buildRsiCitizenLink(spelling);
    window.open(url, "_blank", "noopener,noreferrer");
  }, [candidate.corrected_text, candidate.extracted_name]);

  const validationState = candidate.validation_state ?? "unchecked";
  const validationIcon =
    validationState === "found"
      ? "check_circle"
      : validationState === "not_found"
        ? "person_off"
        : validationState === "checking"
          ? "progress_activity"
          : validationState === "failed"
            ? "error_outline"
            : "help";
  const validationTitle =
    validationState === "found"
      ? "RSI profile found (open profile)"
      : validationState === "not_found"
        ? "RSI profile not found (open profile)"
        : validationState === "checking"
          ? "Checking RSI profile"
          : validationState === "failed"
            ? "RSI validation failed"
            : "RSI profile not checked";
  const canOpenRsiProfile = validationState === "found" || validationState === "not_found";
  return (
    <div
      className="candidate-row"
      ref={rowRef}
      draggable
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      style={{ contain: "layout paint style" }}
    >
      <div className="candidate-main review-candidate-main">
        <div className="candidate-main-left">
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
        </div>
        {resolvedThumbnailSrc ? (
          <button
            type="button"
            className="candidate-inline-thumbnail"
            onClick={handleOpenThumbnail}
            aria-label="Open thumbnail"
            title="Open thumbnail"
          >
            <img
              src={resolvedThumbnailSrc}
              alt={`Thumbnail for ${currentText}`}
            />
          </button>
        ) : (
          <div className="candidate-inline-thumbnail placeholder" aria-hidden="true">
            <span className="material-symbols-outlined">image</span>
          </div>
        )}
        <div className="candidate-status-stack">
          {candidate.marked_new && <span className="status-chip new">New</span>}
          <span className={`status-chip ${currentStatus}`}>{currentStatus.charAt(0).toUpperCase()}{currentStatus.slice(1)}</span>
        </div>
      </div>
      <div className="candidate-meta">
        {isSelected && <span>Selected group name</span>}
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
            onClick={handleSaveEdit}
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
              onClick={handleConfirm}
            >
              Accept
            </button>
            <button
              type="button"
              className={`decision-action${isRejected ? " is-selected" : ""}`}
              onClick={handleReject}
            >
              Reject
            </button>
          </div>
          <div className="candidate-secondary-actions" role="group" aria-label="Candidate tools">
            <button
              type="button"
              className={`ghost-action icon-tool-button validation-state-button validation-state-${validationState}`}
              aria-label={validationTitle}
              title={validationTitle}
              onClick={canOpenRsiProfile ? handleOpenRsiProfile : undefined}
              disabled={!canOpenRsiProfile}
            >
              <span className="material-symbols-outlined" aria-hidden="true">{validationIcon}</span>
            </button>
            {onRecheck && (
              <button
                type="button"
                className="ghost-action icon-tool-button"
                aria-label="Retry RSI check"
                title="Retry RSI check"
                onClick={() => onRecheck(candidate.candidate_id, candidate.corrected_text ?? candidate.extracted_name)}
              >
                <span className="material-symbols-outlined" aria-hidden="true">refresh</span>
              </button>
            )}
            <button
              type="button"
              className="ghost-action icon-tool-button"
              aria-label="Edit candidate"
              title="Edit candidate"
              onClick={handleEdit}
            >
              <span className="material-symbols-outlined" aria-hidden="true">edit</span>
            </button>
            <button
              type="button"
              className="ghost-action icon-tool-button"
              aria-label="Remove candidate"
              title="Remove candidate"
              onClick={handleRemove}
            >
              <span className="material-symbols-outlined" aria-hidden="true">delete</span>
            </button>
          </div>
        </div>
      )}

      {validationError && (
        <ValidationFeedback
          type="error"
          message={validationError.message}
          hint={validationError.hint}
          conflictGroupId={validationError.conflictGroupId}
        />
      )}
    </div>
  );
}

export const CandidateRow = memo(CandidateRowComponent);

