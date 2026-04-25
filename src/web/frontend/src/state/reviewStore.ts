export type ReviewStoreState = {
  selectedSessionId: string | null;
  sessions: Record<string, { csvPath: string; hydratedAt: string; data: unknown }>;
  reopenContext: {
    historyId: string;
    warningMessages: string[];
    hydratedAt: string;
  } | null;
};

export const initialReviewStoreState: ReviewStoreState = {
  selectedSessionId: null,
  sessions: {},
  reopenContext: null,
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
}

export type GroupToggleState = Record<string, boolean>;

export function deriveGroupToggleState(groups: ReviewGroupToggleShape[]): GroupToggleState {
  return groups.reduce<GroupToggleState>((acc, group) => {
    const groupId = String(group.group_id || "").trim();
    if (!groupId) {
      return acc;
    }
    const isResolved = (group.resolution_status ?? "UNRESOLVED") === "RESOLVED";
    acc[groupId] = typeof group.is_collapsed === "boolean" ? group.is_collapsed : isResolved;
    return acc;
  }, {});
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
