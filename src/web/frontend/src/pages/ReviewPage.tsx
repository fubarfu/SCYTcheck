import { useEffect, useMemo, useRef, useState } from "react";
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

interface ReviewPageProps {
  reopenContext?: {
    historyId: string;
    warningMessages: string[];
    hydratedAt: string;
  } | null;
  autoCsvPath?: string | null;
}

export function ReviewPage({ reopenContext = null, autoCsvPath = null }: ReviewPageProps) {
  const [sessions, setSessions] = useState<ReviewSessionSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedSession, setSelectedSession] = useState<ReviewSessionPayload | null>(null);
  const [csvPathInput, setCsvPathInput] = useState("");
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [undoCount, setUndoCount] = useState(0);
  const [filter, setFilter] = useState<ReviewFilterState>({
    searchText: "",
    status: "all",
  });

  const [thumbnailCandidateId, setThumbnailCandidateId] = useState<string | null>(null);
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null);
  const [reopenWarning, setReopenWarning] = useState<string | null>(null);
  const autoLoadedHistoryCsvPathRef = useRef<string | null>(null);

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
  const totalCandidates = selectedSession?.candidates?.length ?? 0;
  const reviewedCandidates = useMemo(
    () => (selectedSession?.candidates ?? []).filter((candidate) => (candidate.status ?? "pending") !== "pending").length,
    [selectedSession?.candidates],
  );

  const refreshSessions = async () => {
    const resp = await fetch("/api/review/sessions");
    if (!resp.ok) return;
    const data = await resp.json() as { sessions: ReviewSessionSummary[] };
    setSessions(data.sessions);
  };

  useEffect(() => {
    const openReview = (event: Event) => {
      const custom = event as CustomEvent<{ csvPath?: string; autoLoad?: boolean }>;
      const csvPath = custom.detail?.csvPath;
      if (csvPath) {
        setCsvPathInput(csvPath);
        if (custom.detail?.autoLoad) {
          void loadSessionFromCsv(csvPath);
        }
      }
    };
    window.addEventListener("scyt:open-review", openReview as EventListener);
    return () => window.removeEventListener("scyt:open-review", openReview as EventListener);
  }, []);

  useEffect(() => {
    const value = autoCsvPath?.trim() ?? "";
    if (value) {
      setCsvPathInput(value);
    }
  }, [autoCsvPath]);

  useEffect(() => {
    const value = autoCsvPath?.trim() ?? "";
    if (!reopenContext || !value) {
      return;
    }
    if (autoLoadedHistoryCsvPathRef.current === value) {
      return;
    }
    autoLoadedHistoryCsvPathRef.current = value;
    void loadSessionFromCsv(value);
  }, [autoCsvPath, reopenContext]);

  useEffect(() => {
    if (!reopenContext) {
      setReopenWarning(null);
      return;
    }
    if (reopenContext.warningMessages.length > 0) {
      setReopenWarning(reopenContext.warningMessages.join(" "));
      return;
    }
    setReopenWarning(null);
  }, [reopenContext]);

  const loadSessionFromCsv = async (csvPathOverride?: string) => {
    setLoadingError(null);
    setExportMessage(null);
    const targetPath = (csvPathOverride ?? csvPathInput).trim();
    if (!targetPath) {
      setLoadingError("csv_path is required");
      return;
    }
    const resp = await fetch("/api/review/sessions/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ csv_path: targetPath }),
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
    setLoadingError(null);
  };

  const postAction = async (action: { action_type: string; target_ids: string[]; payload?: Record<string, unknown> }) => {
    if (!selectedSessionId) return;
    setExportMessage(null);
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
    setExportMessage(null);
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
      setThumbnailUrl(`/api/review/sessions/${selectedSessionId}/thumbnails/${candidateId}.png`);
    } else {
      setThumbnailUrl(null);
    }
    setThumbnailCandidateId(candidateId);
  };

  const exportSession = async () => {
    if (!selectedSessionId) return;
    setExportMessage(null);
    const resp = await fetch(`/api/review/sessions/${selectedSessionId}/export`, { method: "POST" });
    if (!resp.ok) {
      setLoadingError("Export failed");
      return;
    }
    const body = await resp.json() as { deduplicated_names_csv_path: string; occurrences_csv_path: string };
    setExportMessage(
      `Exported deduplicated names to ${body.deduplicated_names_csv_path} and occurrences to ${body.occurrences_csv_path}`,
    );
  };

  return (
    <section className="page-panel">
      <div className="page-heading-row">
        <p className="eyebrow">Review</p>
        <h2>Review detected names</h2>
        <p className="page-subtitle">
          Load one result file, filter what matters, then confirm or reject candidates without the extra noise.
        </p>
      </div>

      {loadingError && <SessionLoadErrorState message={loadingError} onRetry={() => setLoadingError(null)} />}
      {exportMessage && <div className="export-banner">{exportMessage}</div>}
      {reopenWarning && <div className="export-banner">{reopenWarning}</div>}

      <div className="review-stack">
        <div className="panel-card">
          <div className="panel-card-body review-topbar">
            <div className="review-source-picker">
              <label>
                Result file
                <div className="review-load-row">
                  <input
                    type="text"
                    value={csvPathInput}
                    onChange={(e) => setCsvPathInput(e.target.value)}
                    placeholder="C:/output/match.csv"
                  />
                  <button type="button" className="primary-action" onClick={() => { void loadSessionFromCsv(); }}>
                    Load result
                  </button>
                </div>
              </label>
              {sessions.length > 0 && (
                <div className="review-session-strip">
                  {sessions.slice(0, 6).map((s) => (
                    <button
                      key={s.session_id}
                      type="button"
                      className={s.session_id === selectedSessionId ? "session-item active" : "session-item"}
                      onClick={() => { void fetchSession(s.session_id); }}
                    >
                      <span>{s.display_name}</span>
                      <small>{new Date(s.updated_at).toLocaleDateString()}</small>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="review-summary-block">
              <div className="review-progress-meta">
                <span>{reviewedCandidates} / {totalCandidates} reviewed</span>
                <span>{filteredCandidates.length} visible</span>
              </div>
              <progress
                className="review-progress-track"
                value={reviewedCandidates}
                max={Math.max(totalCandidates, 1)}
              />
              <div className="candidate-list-actions">
                <button type="button" className="ghost-action" onClick={() => { void handleUndo(); }} disabled={undoCount <= 0}>
                  Undo
                </button>
                <button type="button" className="primary-action" onClick={() => { void exportSession(); }} disabled={!selectedSessionId}>
                  Export review
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="panel-card">
          <div className="panel-card-body review-filter-shell">
            <ReviewFilterBar
              searchText={filter.searchText}
              status={filter.status}
              onSearchTextChange={(value) => setFilter((prev) => ({ ...prev, searchText: value }))}
              onStatusChange={(value) => setFilter((prev) => ({ ...prev, status: value }))}
            />
          </div>
        </div>

        <div className="candidate-list review-candidate-stack">
          {filteredCandidates.length === 0 ? (
            <div className="panel-card">
              <div className="panel-card-body empty-region-state">
                <div>
                  <strong>No candidates to review yet.</strong>
                  <p>Load a result file or adjust the current filters.</p>
                </div>
              </div>
            </div>
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
