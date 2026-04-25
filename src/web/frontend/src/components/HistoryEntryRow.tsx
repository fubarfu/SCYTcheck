import type { HistoryEntry } from "../state/historyStore";

interface HistoryEntryRowProps {
  entry: HistoryEntry;
  onReopen: (historyId: string) => void;
  onDelete: (historyId: string) => void;
  busy: boolean;
}

export function HistoryEntryRow({ entry, onReopen, onDelete, busy }: HistoryEntryRowProps) {
  const updatedAt = entry.updated_at ? new Date(entry.updated_at).toLocaleString() : "-";

  return (
    <article className="history-entry-row panel-card">
      <div className="panel-card-body history-entry-body">
        <div className="history-entry-main">
          <h3>{entry.display_name}</h3>
          <p className="history-source">{entry.canonical_source}</p>
          <div className="history-meta-row">
            <span>Runs: {entry.run_count}</span>
            <span>Duration: {entry.duration_seconds ?? "unknown"}</span>
            <span>Updated: {updatedAt}</span>
            {entry.potential_duplicate && <span className="history-badge">Potential duplicate</span>}
          </div>
        </div>
        <div className="history-entry-actions">
          <button
            type="button"
            className="primary-action"
            disabled={busy}
            onClick={() => onReopen(entry.history_id)}
          >
            Reopen
          </button>
          <button
            type="button"
            className="ghost-action"
            disabled={busy}
            onClick={() => onDelete(entry.history_id)}
          >
            Delete
          </button>
        </div>
      </div>
    </article>
  );
}
