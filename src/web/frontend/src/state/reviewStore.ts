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
