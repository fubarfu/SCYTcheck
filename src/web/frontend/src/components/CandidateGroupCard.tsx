import { DragEvent, useState } from "react";
import { CandidateRow, type Candidate } from "./CandidateRow";
import {
  clearDraggedCandidate,
  getDropCommitted,
  getDraggedCandidate,
  getDraggedGroupId,
  getHoveredGroupId,
  resetDragSession,
  setDropCommitted,
  setDraggedGroupId,
  setHoveredGroupId,
} from "../state/dragPayload";

const GROUP_DRAG_MIME = "application/x-scyt-group-id";
const CANDIDATE_DRAG_MIME = "application/x-scyt-candidate";
const FALLBACK_DRAG_MIME = "text/plain";

type DragPayload = {
  kind?: "group" | "candidate";
  group_id?: string;
  candidate_id?: string;
  source_group_id?: string | null;
};

function parseFallbackPayload(raw: string): DragPayload | null {
  const text = raw.trim();
  if (!text.startsWith("{")) {
    return null;
  }
  try {
    const parsed = JSON.parse(text) as DragPayload;
    if (parsed.kind !== "group" && parsed.kind !== "candidate") {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export interface CandidateGroup {
  group_id: string;
  display_name: string;
  accepted_name?: string | null;
  accepted_name_summary?: string | null;
  is_collapsed?: boolean;
  remembered_is_collapsed?: boolean | null;
  resolution_status?: string;
  active_spellings?: string[];
  active_candidate_count?: number;
  total_candidate_count?: number;
  occurrence_count?: number;
  is_consensus?: boolean;
  rejected_candidate_ids?: string[];
  group_recommendation_score?: number;
  candidates: Array<Candidate & { temporal_proximity?: number; recommendation_score?: number }>;
}

interface Props {
  group: CandidateGroup;
  selectedSessionId?: string | null;
    projectLocation?: string | null;
  sourceType: "local_file" | "youtube_url";
  sourceValue: string;
  validationFeedback?: {
    candidateId?: string | null;
    message: string;
    hint?: string | null;
    conflictGroupId?: string | null;
  } | null;
  forceExpanded?: boolean;
  hideCollapseControl?: boolean;
  onAction: (action: {
    action_type: string;
    target_ids: string[];
    payload?: Record<string, unknown>;
  }) => void;
  onOpenThumbnail: (candidateId: string) => void;
  onRecheck?: (candidateId: string, spelling: string) => void;
}

export function CandidateGroupCard({
  group,
  selectedSessionId = null,
    projectLocation = null,
  sourceType,
  sourceValue,
  validationFeedback = null,
  forceExpanded = false,
  hideCollapseControl = false,
  onAction,
  onOpenThumbnail,
  onRecheck,
}: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [draggingGroup, setDraggingGroup] = useState(false);
  const normalizeName = (value: string | undefined | null): string => String(value ?? "").trim().toLowerCase();
  const acceptedNormalized = normalizeName(group.accepted_name);
  const selectedCandidateId = group.candidates.find((candidate) => {
    if ((candidate.status ?? "pending") === "confirmed") {
      return true;
    }
    if (!acceptedNormalized) {
      return false;
    }
    return normalizeName(candidate.corrected_text ?? candidate.extracted_name) === acceptedNormalized;
  })?.candidate_id ?? null;

  const isCollapsed = forceExpanded ? false : Boolean(group.is_collapsed);
  const isResolved = (group.resolution_status ?? "UNRESOLVED") === "RESOLVED";
  const hasIssue = !isResolved;
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
      resolution_status: group.resolution_status ?? "UNRESOLVED",
    },
  };

  const handleGroupDragStart = (event: DragEvent<HTMLElement>) => {
    event.stopPropagation();
    if (typeof event.dataTransfer.clearData === "function") {
      event.dataTransfer.clearData();
    }
    const fallback = JSON.stringify({ kind: "group", group_id: group.group_id });
    event.dataTransfer.setData(GROUP_DRAG_MIME, group.group_id);
    event.dataTransfer.setData(FALLBACK_DRAG_MIME, fallback);
    event.dataTransfer.effectAllowed = "move";
    setDropCommitted(false);
    setHoveredGroupId(null);
    clearDraggedCandidate();
    setDraggedGroupId(group.group_id);
    setDraggingGroup(true);
  };

  const handleGroupDragEnd = () => {
    const sourceGroupId = getDraggedGroupId();
    const hoveredTargetGroupId = getHoveredGroupId();
    const didCommit = getDropCommitted();
    if (!didCommit && sourceGroupId && hoveredTargetGroupId && sourceGroupId !== hoveredTargetGroupId) {
      onAction({
        action_type: "merge_groups",
        target_ids: [sourceGroupId],
        payload: {
          source_group_id: sourceGroupId,
          target_group_id: hoveredTargetGroupId,
          group_id: hoveredTargetGroupId,
        },
      });
    }
    resetDragSession();
    setDraggingGroup(false);
    setDragOver(false);
  };

  const handleDragOver = (event: DragEvent<HTMLElement>) => {
    const hasGroup = Array.from(event.dataTransfer.types).includes(GROUP_DRAG_MIME);
    const hasCandidate = Array.from(event.dataTransfer.types).includes(CANDIDATE_DRAG_MIME);
    const fallbackPayload = parseFallbackPayload(event.dataTransfer.getData(FALLBACK_DRAG_MIME));
    const hasFallback = Boolean(fallbackPayload);
    const hasActiveGroup = Boolean(getDraggedGroupId());
    const hasActiveCandidate = Boolean(getDraggedCandidate());
    if (!hasGroup && !hasCandidate && !hasFallback && !hasActiveGroup && !hasActiveCandidate) {
      return;
    }
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    setHoveredGroupId(group.group_id);
    setDragOver(true);
  };

  const handleDrop = (event: DragEvent<HTMLElement>) => {
    event.preventDefault();
    setDragOver(false);

    const fallbackPayload = parseFallbackPayload(event.dataTransfer.getData(FALLBACK_DRAG_MIME));

    const draggedGroupId = (
      event.dataTransfer.getData(GROUP_DRAG_MIME).trim()
      || (fallbackPayload?.kind === "group" ? String(fallbackPayload.group_id ?? "").trim() : "")
      || (getDraggedGroupId() ?? "")
    );
    if (draggedGroupId && draggedGroupId !== group.group_id) {
      setDropCommitted(true);
      onAction({
        action_type: "merge_groups",
        target_ids: [draggedGroupId],
        payload: {
          source_group_id: draggedGroupId,
          target_group_id: group.group_id,
          group_id: group.group_id,
        },
      });
      return;
    }

    const draggedCandidate = (
      event.dataTransfer.getData(CANDIDATE_DRAG_MIME).trim()
      || (fallbackPayload?.kind === "candidate" ? JSON.stringify(fallbackPayload) : "")
      || (() => {
        const active = getDraggedCandidate();
        return active ? JSON.stringify({ kind: "candidate", ...active }) : "";
      })()
    );
    if (!draggedCandidate) {
      return;
    }

    try {
      const payload = JSON.parse(draggedCandidate) as { candidate_id?: string; source_group_id?: string | null };
      const candidateId = String(payload.candidate_id ?? "").trim();
      if (!candidateId) {
        return;
      }
      onAction({
        action_type: "move_candidate",
        target_ids: [candidateId],
        payload: {
          candidate_id: candidateId,
          source_group_id: payload.source_group_id ?? null,
          to_group_id: group.group_id,
          group_id: group.group_id,
        },
      });
      setDropCommitted(true);
      clearDraggedCandidate();
    } catch {
      // Ignore malformed drag payload.
    }
  };

  return (
    <section
      className={`${isResolved ? "candidate-group-card group-resolved" : "candidate-group-card group-unresolved"}${dragOver ? " group-drop-target" : ""}${draggingGroup ? " group-dragging" : ""}`}
      data-testid={`candidate-group-${group.group_id}`}
      data-collapsed={isCollapsed ? "true" : "false"}
      data-resolution={isResolved ? "resolved" : "unresolved"}
      onDragOver={handleDragOver}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      <header
        className={isResolved ? "group-card-header" : "group-card-header group-card-header-unresolved"}
      >
        <button
          type="button"
          className="group-drag-handle"
          aria-label="Drag group to merge"
          draggable
          onDragStart={handleGroupDragStart}
          onDragEnd={handleGroupDragEnd}
        >
          ::
        </button>
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
          {!hideCollapseControl && (
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
          )}
          {!isCollapsed && (
            <button
              type="button"
              className="ghost-action"
              onClick={() => onAction({
                action_type: "deselect",
                target_ids: [],
                payload: { group_id: group.group_id },
              })}
            >
              Reset
            </button>
          )}
        </div>
      </header>
      {!isCollapsed && (
        <div className="group-candidate-list">
          {group.candidates.map((candidate, index) => (
            <CandidateRow
              key={candidate.candidate_id}
              candidate={candidate}
              groupId={group.group_id}
              selectedCandidateId={selectedCandidateId}
              sourceType={sourceType}
              sourceValue={sourceValue}
              occurrenceIndex={index + 1}
              occurrenceCount={occurrenceCount}
              showOccurrenceMetadata={isResolved}
              validationError={
                validationFeedback && (!validationFeedback.candidateId || validationFeedback.candidateId === candidate.candidate_id)
                  ? {
                      message: validationFeedback.message,
                      hint: validationFeedback.hint,
                      conflictGroupId: validationFeedback.conflictGroupId,
                    }
                  : null
              }
              onAction={onAction}
              onOpenThumbnail={onOpenThumbnail}
              onRecheck={onRecheck}
              thumbnailCheckUrl={selectedSessionId ? `/api/review/sessions/${selectedSessionId}/thumbnails/${candidate.candidate_id}${projectLocation ? `?pl=${encodeURIComponent(projectLocation)}` : ""}` : null}
            />
          ))}
        </div>
      )}
    </section>
  );
}
