import { DragEvent, useState } from "react";
import type { CandidateGroup } from "./CandidateGroupCard";
import {
  clearDraggedCandidate,
  getDraggedCandidate,
  getDraggedGroupId,
  setDropCommitted,
  setHoveredGroupId,
} from "../state/dragPayload";

const GROUP_DRAG_MIME = "application/x-scyt-group-id";
const CANDIDATE_DRAG_MIME = "application/x-scyt-candidate";
const FALLBACK_DRAG_MIME = "text/plain";

function parseGroupFallbackPayload(raw: string): { group_id?: string } | null {
  const text = raw.trim();
  if (!text.startsWith("{")) {
    return null;
  }
  try {
    const payload = JSON.parse(text) as { kind?: string; group_id?: string };
    if (payload.kind !== "group") {
      return null;
    }
    return { group_id: payload.group_id };
  } catch {
    return null;
  }
}

function parseCandidateFallbackPayload(raw: string): { candidate_id?: string; source_group_id?: string | null } | null {
  const text = raw.trim();
  if (!text.startsWith("{")) {
    return null;
  }
  try {
    const payload = JSON.parse(text) as {
      kind?: string;
      candidate_id?: string;
      source_group_id?: string | null;
    };
    if (payload.kind !== "candidate") {
      return null;
    }
    return {
      candidate_id: payload.candidate_id,
      source_group_id: payload.source_group_id ?? null,
    };
  } catch {
    return null;
  }
}

interface Props {
  group: CandidateGroup;
  isSelected: boolean;
  hasValidationError?: boolean;
  onSelect: (groupId: string) => void;
  onMergeGroups: (sourceGroupId: string, targetGroupId: string) => void;
  onMoveCandidate: (candidateId: string, sourceGroupId: string | null, targetGroupId: string) => void;
}

/**
 * Compact entry shown in the left "groups rail" of the review workspace.
 * Mirrors the Stitch designs: status pill (Resolved / Unresolved / Conflict) plus
 * a count of matched candidates.
 */
export function GroupListItem({
  group,
  isSelected,
  hasValidationError = false,
  onSelect,
  onMergeGroups,
  onMoveCandidate,
}: Props) {
  const [isDropTarget, setIsDropTarget] = useState(false);
  const isResolved = (group.resolution_status ?? "UNRESOLVED") === "RESOLVED";
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
    statusLabel = "Unresolved";
    statusVariant = "status-error";
  } else if (isResolved) {
    statusLabel = "Resolved";
    statusVariant = "status-resolved";
  }

  const subtitle = isResolved && acceptedSummary
    ? acceptedSummary
    : `${candidateCount} candidate${candidateCount === 1 ? "" : "s"} matched`;

  const handleDragOver = (event: DragEvent<HTMLButtonElement>) => {
    const types = Array.from(event.dataTransfer.types);
    const hasGroupMime = types.includes(GROUP_DRAG_MIME);
    const hasCandidateMime = types.includes(CANDIDATE_DRAG_MIME);
    const groupFallbackPayload = parseGroupFallbackPayload(event.dataTransfer.getData(FALLBACK_DRAG_MIME));
    const candidateFallbackPayload = parseCandidateFallbackPayload(event.dataTransfer.getData(FALLBACK_DRAG_MIME));
    const activeGroupId = getDraggedGroupId();
    const activeCandidate = getDraggedCandidate();
    
    if (!hasGroupMime && !hasCandidateMime && !groupFallbackPayload && !candidateFallbackPayload && !activeGroupId && !activeCandidate) {
      return;
    }
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    setHoveredGroupId(group.group_id);
    setIsDropTarget(true);
  };

  const handleDragLeave = () => {
    setIsDropTarget(false);
    setHoveredGroupId(null);
  };

  const handleDrop = (event: DragEvent<HTMLButtonElement>) => {
    event.preventDefault();
    setIsDropTarget(false);

    const groupFallbackPayload = parseGroupFallbackPayload(event.dataTransfer.getData(FALLBACK_DRAG_MIME));
    const draggedGroupId = (
      event.dataTransfer.getData(GROUP_DRAG_MIME).trim()
      || String(groupFallbackPayload?.group_id ?? "").trim()
      || String(getDraggedGroupId() ?? "").trim()
    );

    if (draggedGroupId && draggedGroupId !== group.group_id) {
      setDropCommitted(true);
      setHoveredGroupId(null);
      onMergeGroups(draggedGroupId, group.group_id);
      return;
    }

    const candidateMimePayload = parseCandidateFallbackPayload(event.dataTransfer.getData(CANDIDATE_DRAG_MIME));
    const candidateFallbackPayload = parseCandidateFallbackPayload(event.dataTransfer.getData(FALLBACK_DRAG_MIME));
    const activeCandidate = getDraggedCandidate();
    const draggedCandidateId = String(
      candidateMimePayload?.candidate_id
      || candidateFallbackPayload?.candidate_id
      || activeCandidate?.candidate_id
      || "",
    ).trim();
    const sourceGroupId = candidateMimePayload?.source_group_id
      ?? candidateFallbackPayload?.source_group_id
      ?? activeCandidate?.source_group_id
      ?? null;

    setHoveredGroupId(null);
    if (!draggedCandidateId || sourceGroupId === group.group_id) {
      return;
    }
    setDropCommitted(true);
    clearDraggedCandidate();
    onMoveCandidate(draggedCandidateId, sourceGroupId, group.group_id);
  };
  return (
    <button
      type="button"
      className={`group-rail-item${isSelected ? " is-selected" : ""}${hasValidationError || hasIssue ? " has-issue" : ""}${isDropTarget ? " is-drop-target" : ""}`}
      data-testid={`group-rail-item-${group.group_id}`}
      data-status={statusVariant}
      data-selected={isSelected ? "true" : "false"}
      onClick={() => onSelect(group.group_id)}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
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
