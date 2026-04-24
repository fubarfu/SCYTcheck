export type ReviewStoreState = {
  selectedSessionId: string | null;
  sessions: Record<string, { csvPath: string; hydratedAt: string; data: unknown }>;
};

export const initialReviewStoreState: ReviewStoreState = {
  selectedSessionId: null,
  sessions: {},
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
