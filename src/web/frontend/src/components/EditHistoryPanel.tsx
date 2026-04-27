import type { EditHistoryEntry } from "../state/reviewStore";

interface EditHistoryPanelProps {
  entries: EditHistoryEntry[];
  selectedEntryId: string | null;
  restoredEntryId: string | null;
  busy: boolean;
  error: string | null;
  onSelectEntry: (entryId: string) => void;
  onRestoreEntry: (entryId: string) => void;
}

function formatTimestamp(value: string): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function EditHistoryPanel({
  entries,
  selectedEntryId,
  restoredEntryId,
  busy,
  error,
  onSelectEntry,
  onRestoreEntry,
}: EditHistoryPanelProps) {
  return (
    <div className="panel-card edit-history-panel">
      <div className="panel-card-header edit-history-header">
        <div>
          <h3>Edit History</h3>
          <p className="edit-history-subtitle">Snapshots are append-only and restorable.</p>
        </div>
      </div>
      <div className="panel-card-body edit-history-body">
        {error && <p className="edit-history-error">{error}</p>}
        {entries.length === 0 ? (
          <p className="edit-history-empty">No history entries yet. State-changing actions will appear here.</p>
        ) : (
          <ul className="edit-history-list" aria-label="Edit history entries">
            {entries.map((entry) => {
              const isSelected = entry.entry_id === selectedEntryId;
              const isRestored = entry.entry_id === restoredEntryId;
              const rowClassName = [
                "edit-history-row",
                isSelected ? "is-selected" : "",
                isRestored ? "is-restored" : "",
              ]
                .filter(Boolean)
                .join(" ");
              return (
                <li key={entry.entry_id}>
                  <button
                    type="button"
                    className={rowClassName}
                    onClick={() => onSelectEntry(entry.entry_id)}
                    disabled={busy}
                  >
                    <div className="edit-history-row-main">
                      <div className="edit-history-row-title">
                        <strong>{formatTimestamp(entry.created_at)}</strong>
                        {entry.compressed && <span className="history-badge">Compressed</span>}
                        {isRestored && <span className="history-badge">Restored</span>}
                      </div>
                      <p className="edit-history-row-meta">
                        Trigger: {entry.trigger_type || "unknown"} · Groups: {entry.group_count} · Resolved: {entry.resolved_count} · Unresolved: {entry.unresolved_count}
                      </p>
                    </div>
                    <span className="edit-history-action-label">Select</span>
                  </button>
                  <div className="edit-history-row-actions">
                    <button
                      type="button"
                      className="ghost-action"
                      disabled={busy}
                      onClick={() => onRestoreEntry(entry.entry_id)}
                    >
                      Restore snapshot
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
