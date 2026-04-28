import { useState } from "react";
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

const RESTORE_WARNING_MESSAGE = "Restore this snapshot? All changes made after this point and all newer snapshots will be deleted.";

export function EditHistoryPanel({
  entries,
  selectedEntryId,
  restoredEntryId,
  busy,
  error,
  onSelectEntry,
  onRestoreEntry,
}: EditHistoryPanelProps) {
  const [pendingRestoreEntryId, setPendingRestoreEntryId] = useState<string | null>(null);

  const confirmRestore = () => {
    if (!pendingRestoreEntryId) {
      return;
    }
    onRestoreEntry(pendingRestoreEntryId);
    setPendingRestoreEntryId(null);
  };

  return (
    <details className="panel-card edit-history-panel">
      <summary className="panel-card-header edit-history-header" data-testid="edit-history-summary">
        <div>
          <h3>Edit History</h3>
          <p className="edit-history-subtitle">Restoring a snapshot deletes newer history entries after confirmation.</p>
        </div>
      </summary>
      <div className="panel-card-body edit-history-body">
        {error && <p className="edit-history-error">{error}</p>}
        {entries.length === 0 ? (
          <p className="edit-history-empty">No history entries yet. State-changing actions will appear here.</p>
        ) : (
          <>
            <div className="edit-history-table-head" aria-hidden="true">
              <span>Snapshot</span>
              <span>Trigger</span>
              <span>Groups</span>
              <span>Resolved</span>
              <span>Unresolved</span>
            </div>
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
                <li key={entry.entry_id} className="edit-history-item">
                  <div className="edit-history-row-shell">
                    <button
                      type="button"
                      className={rowClassName}
                      onClick={() => onSelectEntry(entry.entry_id)}
                      disabled={busy}
                    >
                      <span className="edit-history-cell edit-history-cell-time">
                        <strong>{formatTimestamp(entry.created_at)}</strong>
                        <span className="edit-history-cell-badges">
                          {entry.compressed && <span className="history-badge">Compressed</span>}
                          {isRestored && <span className="history-badge">Restored</span>}
                        </span>
                      </span>
                      <span className="edit-history-cell">{entry.trigger_type || "unknown"}</span>
                      <span className="edit-history-cell edit-history-cell-num">{entry.group_count}</span>
                      <span className="edit-history-cell edit-history-cell-num">{entry.resolved_count}</span>
                      <span className="edit-history-cell edit-history-cell-num">{entry.unresolved_count}</span>
                    </button>
                    <button
                      type="button"
                      className="ghost-action icon-tool-button edit-history-restore-icon"
                      disabled={busy}
                      onClick={() => setPendingRestoreEntryId(entry.entry_id)}
                      aria-label="Restore snapshot"
                      title="Restore snapshot"
                    >
                      <span className="material-symbols-outlined" aria-hidden="true">
                        restore
                      </span>
                    </button>
                  </div>
                </li>
              );
            })}
            </ul>
          </>
        )}
      </div>
      {pendingRestoreEntryId && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Restore snapshot warning">
          <div className="modal-panel restore-confirmation-modal">
            <h3>Restore snapshot</h3>
            <p>{RESTORE_WARNING_MESSAGE}</p>
            <div className="modal-actions">
              <button type="button" className="ghost-action" onClick={() => setPendingRestoreEntryId(null)}>
                Cancel
              </button>
              <button type="button" className="primary-action" onClick={confirmRestore}>
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </details>
  );
}
