import { useEffect, useMemo, useState } from "react";
import { CandidateRow, type Candidate } from "../components/CandidateRow";
import { FrameThumbnailModal } from "../components/FrameThumbnailModal";
import { ReviewFilterBar } from "../components/ReviewFilterBar";
import { SessionLoadErrorState } from "../components/SessionLoadErrorState";
import {
  selectFilteredCandidates,
  selectVisibleCandidateIds,
  type ReviewFilterState,
} from "../state/reviewSelectors";

interface ReviewSessionSummary {
  session_id: string;
  display_name: string;
  csv_path: string;
  updated_at: string;
}

interface ReviewSessionPayload {
  session_id: string;
  csv_path: string;
  source_type?: "local_file" | "youtube_url";
  source_value?: string;
  candidates?: Candidate[];
}

export function ReviewPage() {
  const [sessions, setSessions] = useState<ReviewSessionSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedSession, setSelectedSession] = useState<ReviewSessionPayload | null>(null);
  const [csvPathInput, setCsvPathInput] = useState("");
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [undoCount, setUndoCount] = useState(0);
  const [filter, setFilter] = useState<ReviewFilterState>({
    searchText: "",
    status: "all",
  });

  const [thumbnailCandidateId, setThumbnailCandidateId] = useState<string | null>(null);
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null);

  const sourceType = selectedSession?.source_type ?? "local_file";
  const sourceValue = selectedSession?.source_value ?? "";

  const selectedCandidate = useMemo(
    () => (thumbnailCandidateId
      ? selectedSession?.candidates?.find((c) => c.candidate_id === thumbnailCandidateId) ?? null
      : null),
    [thumbnailCandidateId, selectedSession?.candidates],
  );
  const filteredCandidates = useMemo(
    () => selectFilteredCandidates(selectedSession?.candidates ?? [], filter),
    [selectedSession?.candidates, filter],
  );

  const refreshSessions = async () => {
    const resp = await fetch("/api/review/sessions");
    if (!resp.ok) return;
    const data = await resp.json() as { sessions: ReviewSessionSummary[] };
    setSessions(data.sessions);
  };

  useEffect(() => {
    void refreshSessions();
  }, []);

  useEffect(() => {
    const openReview = (event: Event) => {
      const custom = event as CustomEvent<{ csvPath?: string }>;
      const csvPath = custom.detail?.csvPath;
      if (csvPath) {
        setCsvPathInput(csvPath);
      }
    };
    window.addEventListener("scyt:open-review", openReview as EventListener);
    return () => window.removeEventListener("scyt:open-review", openReview as EventListener);
  }, []);

  const loadSessionFromCsv = async () => {
    setLoadingError(null);
    const resp = await fetch("/api/review/sessions/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ csv_path: csvPathInput.trim() }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ message: "Unable to load session" })) as { message?: string };
      setLoadingError(err.message ?? "Unable to load session");
      return;
    }
    const body = await resp.json() as { session_id: string };
    setSelectedSessionId(body.session_id);
    await refreshSessions();
    await fetchSession(body.session_id);
  };

  const fetchSession = async (sessionId: string) => {
    const resp = await fetch(`/api/review/sessions/${sessionId}`);
    if (!resp.ok) return;
    const session = await resp.json() as ReviewSessionPayload;
    setSelectedSession(session);
    setSelectedSessionId(sessionId);
  };

  const postAction = async (action: { action_type: string; target_ids: string[]; payload?: Record<string, unknown> }) => {
    if (!selectedSessionId) return;
    const resp = await fetch(`/api/review/sessions/${selectedSessionId}/actions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(action),
    });
    if (!resp.ok) {
      setLoadingError("Action failed");
      return;
    }
    setUndoCount((v) => v + 1);
    await fetchSession(selectedSessionId);
  };

  const handleUndo = async () => {
    if (!selectedSessionId) return;
    const resp = await fetch(`/api/review/sessions/${selectedSessionId}/undo`, { method: "POST" });
    if (!resp.ok) {
      setLoadingError("Undo failed");
      return;
    }
    const body = await resp.json() as { remaining_undo_count: number };
    setUndoCount(body.remaining_undo_count);
    await fetchSession(selectedSessionId);
  };

  const openThumbnail = async (candidateId: string) => {
    if (!selectedSessionId) return;
    const resp = await fetch(`/api/review/sessions/${selectedSessionId}/thumbnails/${candidateId}`);
    if (resp.ok) {
      const body = await resp.json() as { thumbnail_url: string };
      setThumbnailUrl(body.thumbnail_url);
    } else {
      setThumbnailUrl(null);
    }
    setThumbnailCandidateId(candidateId);
  };

  const exportSession = async () => {
    if (!selectedSessionId) return;
    const resp = await fetch(`/api/review/sessions/${selectedSessionId}/export`, { method: "POST" });
    if (!resp.ok) {
      setLoadingError("Export failed");
      return;
    }
    const body = await resp.json() as { deduplicated_names_csv_path: string; occurrences_csv_path: string };
    alert(`Exported:\n${body.deduplicated_names_csv_path}\n${body.occurrences_csv_path}`);
  };

  return (
    <section className="page-panel">
      <h2>Review</h2>

      <div className="review-toolbar">
        <input
          type="text"
          value={csvPathInput}
          onChange={(e) => setCsvPathInput(e.target.value)}
          placeholder="C:/output/match.csv"
        />
        <button type="button" className="primary-action" onClick={() => { void loadSessionFromCsv(); }}>
          Load CSV
        </button>
      </div>

      {loadingError && <SessionLoadErrorState message={loadingError} onRetry={() => setLoadingError(null)} />}

      <div className="review-layout">
        <aside className="session-list">
          <h3>Sessions</h3>
          {sessions.map((s) => (
            <button
              key={s.session_id}
              type="button"
              className={s.session_id === selectedSessionId ? "session-item active" : "session-item"}
              onClick={() => { void fetchSession(s.session_id); }}
            >
              <span>{s.display_name}</span>
              <small>{new Date(s.updated_at).toLocaleString()}</small>
            </button>
          ))}
        </aside>

        <div className="candidate-list">
          <div className="candidate-list-head">
            <h3>Candidates</h3>
            <div className="candidate-list-actions">
              <button type="button" onClick={() => { void handleUndo(); }} disabled={undoCount <= 0}>Undo</button>
              <button type="button" className="primary-action" onClick={() => { void exportSession(); }}>
                Export
              </button>
            </div>
          </div>

          <ReviewFilterBar
            searchText={filter.searchText}
            status={filter.status}
            onSearchTextChange={(value) => setFilter((prev) => ({ ...prev, searchText: value }))}
            onStatusChange={(value) => setFilter((prev) => ({ ...prev, status: value }))}
          />

          {filteredCandidates.length === 0 ? (
            <p>No candidates loaded.</p>
          ) : (
            filteredCandidates.map((c) => (
              <CandidateRow
                key={c.candidate_id}
                candidate={c}
                sourceType={sourceType}
                sourceValue={sourceValue}
                onAction={(action) => {
                  if (action.target_ids.length > 1) {
                    const visibleIds = selectVisibleCandidateIds(
                      selectedSession?.candidates ?? [],
                      filter,
                    );
                    action.target_ids = action.target_ids.filter((id) => visibleIds.includes(id));
                  }
                  void postAction(action);
                }}
                onOpenThumbnail={(id) => { void openThumbnail(id); }}
              />
            ))
          )}
        </div>
      </div>

      {thumbnailCandidateId && (
        <FrameThumbnailModal
          candidateId={thumbnailCandidateId}
          thumbnailUrl={thumbnailUrl}
          metadata={{
            timestamp: selectedCandidate?.start_timestamp,
            sourceType,
          }}
          onClose={() => {
            setThumbnailCandidateId(null);
            setThumbnailUrl(null);
          }}
        />
      )}
    </section>
  );
}
