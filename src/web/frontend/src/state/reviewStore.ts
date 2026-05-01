export interface EditHistoryEntry {
  entry_id: string;
  created_at: string;
  group_count: number;
  resolved_count: number;
  unresolved_count: number;
  trigger_type: string;
  compressed: boolean;
}

export interface EditHistoryState {
  entries: EditHistoryEntry[];
  selectedEntryId: string | null;
  restoredEntryId: string | null;
  loading: boolean;
  error: string | null;
}

export type ReviewStoreState = {
  selectedSessionId: string | null;
  sessions: Record<string, { csvPath: string; hydratedAt: string; data: unknown }>;
  reopenContext: {
    historyId: string;
    warningMessages: string[];
    hydratedAt: string;
  } | null;
  editHistory: EditHistoryState;
};

export const initialReviewStoreState: ReviewStoreState = {
  selectedSessionId: null,
  sessions: {},
  reopenContext: null,
  editHistory: {
    entries: [],
    selectedEntryId: null,
    restoredEntryId: null,
    loading: false,
    error: null,
  },
};

export function hydrateSession(
  state: ReviewStoreState,
  sessionId: string,
  csvPath: string,
  data: unknown,
): ReviewStoreState {
  return {
    ...state,
    selectedSessionId: sessionId,
    sessions: {
      ...state.sessions,
      [sessionId]: {
        csvPath,
        hydratedAt: new Date().toISOString(),
        data,
      },
    },
  };
}

export function switchSession(state: ReviewStoreState, sessionId: string): ReviewStoreState {
  if (!(sessionId in state.sessions)) {
    return state;
  }
  return {
    ...state,
    selectedSessionId: sessionId,
  };
}

export function hydrateEditHistoryEntries(
  state: ReviewStoreState,
  entries: EditHistoryEntry[],
): ReviewStoreState {
  const nextSelected =
    state.editHistory.selectedEntryId && entries.some((entry) => entry.entry_id === state.editHistory.selectedEntryId)
      ? state.editHistory.selectedEntryId
      : entries[0]?.entry_id ?? null;
  return {
    ...state,
    editHistory: {
      ...state.editHistory,
      entries,
      selectedEntryId: nextSelected,
      loading: false,
      error: null,
    },
  };
}

export function selectEditHistoryEntry(state: ReviewStoreState, entryId: string): ReviewStoreState {
  return {
    ...state,
    editHistory: {
      ...state.editHistory,
      selectedEntryId: entryId,
    },
  };
}

export function markRestoredHistoryEntry(state: ReviewStoreState, entryId: string): ReviewStoreState {
  return {
    ...state,
    editHistory: {
      ...state.editHistory,
      restoredEntryId: entryId,
      selectedEntryId: entryId,
    },
  };
}
export interface ReopenHydrationPayload {
  history_id: string;
  derived_results?: {
    resolution_messages?: string[];
  };
}

export interface ReviewGroupToggleShape {
  group_id: string;
  resolution_status?: string;
  is_collapsed?: boolean;
  remembered_is_collapsed?: boolean | null;
  accepted_name?: string | null;
  rejected_candidate_ids?: string[];
  candidates?: Array<{
    candidate_id: string;
    extracted_name?: string;
    corrected_text?: string;
    status?: "pending" | "confirmed" | "rejected";
  }>;
}

export type GroupToggleState = Record<string, boolean>;

export function deriveGroupToggleState(groups: ReviewGroupToggleShape[]): GroupToggleState {
  return groups.reduce<GroupToggleState>((acc, group) => {
    const groupId = String(group.group_id || "").trim();
    if (!groupId) {
      return acc;
    }
    const isResolved = (group.resolution_status ?? "UNRESOLVED") === "RESOLVED";
    if (typeof group.is_collapsed === "boolean") {
      acc[groupId] = group.is_collapsed;
      return acc;
    }
    if (typeof group.remembered_is_collapsed === "boolean") {
      acc[groupId] = group.remembered_is_collapsed;
      return acc;
    }
    acc[groupId] = isResolved;
    return acc;
  }, {});
}

function normalizeName(value: string | null | undefined): string {
  return String(value ?? "").trim().toLowerCase();
}

export function reconcileGroupMutationState<T extends { groups?: ReviewGroupToggleShape[] }>(session: T): T {
  if (!Array.isArray(session.groups)) {
    return session;
  }

  return {
    ...session,
    groups: session.groups.map((group) => {
      const accepted = normalizeName(group.accepted_name ?? null);
      const rejected = new Set((group.rejected_candidate_ids ?? []).map((item) => String(item)));
      const candidates = (group.candidates ?? []).map((candidate) => {
        const candidateId = String(candidate.candidate_id ?? "");
        const candidateName = normalizeName(candidate.corrected_text ?? candidate.extracted_name ?? "");
        let nextStatus: "pending" | "confirmed" | "rejected" = "pending";
        if (rejected.has(candidateId)) {
          nextStatus = "rejected";
        } else if (accepted && candidateName === accepted) {
          nextStatus = "confirmed";
        }
        return {
          ...candidate,
          status: nextStatus,
        };
      });

      const hasAccepted = Boolean(accepted);
      const resolved = group.resolution_status ?? (hasAccepted ? "RESOLVED" : "UNRESOLVED");
      const nextCollapsed =
        typeof group.is_collapsed === "boolean"
          ? group.is_collapsed
          : typeof group.remembered_is_collapsed === "boolean"
            ? group.remembered_is_collapsed
          : resolved === "RESOLVED";
      return {
        ...group,
        candidates,
        resolution_status: resolved,
        // Preserve explicitly persisted/manual toggle state whenever available.
        is_collapsed: nextCollapsed,
      };
    }),
  };
}

export function applyGroupToggleState<T extends { groups?: ReviewGroupToggleShape[] }>(
  session: T,
  toggles: GroupToggleState,
): T {
  if (!Array.isArray(session.groups)) {
    return session;
  }
  return {
    ...session,
    groups: session.groups.map((group) => {
      const groupId = String(group.group_id || "").trim();
      if (!groupId || !(groupId in toggles)) {
        const isResolved = (group.resolution_status ?? "UNRESOLVED") === "RESOLVED";
        return {
          ...group,
          is_collapsed: typeof group.is_collapsed === "boolean" ? group.is_collapsed : isResolved,
        };
      }
      return {
        ...group,
        is_collapsed: toggles[groupId],
      };
    }),
  };
}

export function updateGroupToggleState(
  state: GroupToggleState,
  groupId: string,
  isCollapsed: boolean,
): GroupToggleState {
  return {
    ...state,
    [groupId]: isCollapsed,
  };
}

export function hydrateFromReopen(
  state: ReviewStoreState,
  payload: ReopenHydrationPayload,
): ReviewStoreState {
  return {
    ...state,
    reopenContext: {
      historyId: payload.history_id,
      warningMessages: payload.derived_results?.resolution_messages ?? [],
      hydratedAt: new Date().toISOString(),
    },
  };
}
