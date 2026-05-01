type CandidateDragPayload = {
  candidate_id: string;
  source_group_id?: string | null;
};

let activeGroupId: string | null = null;
let activeCandidate: CandidateDragPayload | null = null;
let hoveredGroupId: string | null = null;
let hoveredNewGroupZone = false;
let dropCommitted = false;

export function setDraggedGroupId(groupId: string | null): void {
  activeGroupId = groupId && groupId.trim() ? groupId.trim() : null;
}

export function getDraggedGroupId(): string | null {
  return activeGroupId;
}

export function clearDraggedGroupId(): void {
  activeGroupId = null;
}

export function setDraggedCandidate(payload: CandidateDragPayload | null): void {
  if (!payload) {
    activeCandidate = null;
    return;
  }
  const candidateId = String(payload.candidate_id ?? "").trim();
  if (!candidateId) {
    activeCandidate = null;
    return;
  }
  activeCandidate = {
    candidate_id: candidateId,
    source_group_id: payload.source_group_id ?? null,
  };
}

export function getDraggedCandidate(): CandidateDragPayload | null {
  return activeCandidate;
}

export function clearDraggedCandidate(): void {
  activeCandidate = null;
}

export function setHoveredGroupId(groupId: string | null): void {
  hoveredGroupId = groupId && groupId.trim() ? groupId.trim() : null;
  if (hoveredGroupId) {
    hoveredNewGroupZone = false;
  }
}

export function getHoveredGroupId(): string | null {
  return hoveredGroupId;
}

export function setHoveredNewGroupZone(isActive: boolean): void {
  hoveredNewGroupZone = Boolean(isActive);
  if (hoveredNewGroupZone) {
    hoveredGroupId = null;
  }
}

export function getHoveredNewGroupZone(): boolean {
  return hoveredNewGroupZone;
}

export function setDropCommitted(value: boolean): void {
  dropCommitted = Boolean(value);
}

export function getDropCommitted(): boolean {
  return dropCommitted;
}

export function resetDragSession(): void {
  activeGroupId = null;
  activeCandidate = null;
  hoveredGroupId = null;
  hoveredNewGroupZone = false;
  dropCommitted = false;
}
