import { useEffect, useState } from "react";
import { HistoryEntryRow } from "../components/HistoryEntryRow";
import {
  deleteHistory,
  initialHistoryStoreState,
  listHistory,
  reopenHistory,
  type ReopenResponse,
} from "../state/historyStore";

interface HistoryPageProps {
  onReopenToReview: (payload: ReopenResponse) => void;
}

export function HistoryPage({ onReopenToReview }: HistoryPageProps) {
  const [state, setState] = useState(initialHistoryStoreState);
  const [busyId, setBusyId] = useState<string | null>(null);

  const refresh = async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const response = await listHistory();
      setState({
        items: response.items,
        total: response.total,
        loading: false,
        error: null,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to load history";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const handleReopen = async (historyId: string) => {
    setBusyId(historyId);
    setState((prev) => ({ ...prev, error: null }));
    try {
      const payload = await reopenHistory(historyId);
      onReopenToReview(payload);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to open entry";
      setState((prev) => ({ ...prev, error: message }));
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async (historyId: string) => {
    setBusyId(historyId);
    setState((prev) => ({ ...prev, error: null }));
    try {
      await deleteHistory(historyId);
      await refresh();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to delete entry";
      setState((prev) => ({ ...prev, error: message }));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section className="page-panel">
      <div className="page-heading-row">
        <h2>Manage analyzed videos</h2>
        <p className="page-subtitle">
          Open prior analyses instantly, or remove entries from the managed list without touching files on disk.
        </p>
      </div>

      {state.error && <div className="session-load-error">{state.error}</div>}

      <div className="history-list">
        {state.loading && <div className="panel-card"><div className="panel-card-body">Loading history…</div></div>}

        {!state.loading && state.items.length === 0 && (
          <div className="panel-card">
            <div className="panel-card-body empty-region-state">
              <div>
                <strong>No analyzed videos yet.</strong>
                <p>Run at least one analysis to populate this history list.</p>
              </div>
            </div>
          </div>
        )}

        {!state.loading && state.items.map((entry) => (
          <HistoryEntryRow
            key={entry.history_id}
            entry={entry}
            busy={busyId === entry.history_id}
            onReopen={handleReopen}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </section>
  );
}
