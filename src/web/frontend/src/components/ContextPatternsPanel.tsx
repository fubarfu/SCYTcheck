interface ContextPattern {
  id?: string;
  before_text?: string | null;
  after_text?: string | null;
  enabled?: boolean;
}

interface Settings {
  context_patterns?: ContextPattern[];
}

interface Props {
  settings: Settings;
  onChange: (updated: Settings) => void;
}

export function ContextPatternsPanel({ settings, onChange }: Props) {
  const contextPatterns = settings.context_patterns ?? [];

  const update = (patterns: ContextPattern[]) => {
    onChange({ ...settings, context_patterns: patterns });
  };

  const updatePattern = (index: number, partial: Partial<ContextPattern>) => {
    update(
      contextPatterns.map((pattern, patternIndex) =>
        patternIndex === index ? { ...pattern, ...partial } : pattern,
      ),
    );
  };

  const addPattern = () => {
    update([
      ...contextPatterns,
      {
        id: `custom-${Date.now()}`,
        before_text: "",
        after_text: "",
        enabled: true,
      },
    ]);
  };

  const removePattern = (index: number) => {
    update(contextPatterns.filter((_, patternIndex) => patternIndex !== index));
  };

  return (
    <details className="settings-panel context-patterns-panel">
      <summary>Text patterns</summary>

      <div className="context-patterns-body">
        {contextPatterns.length === 0 ? (
          <p className="modal-hint">No context patterns configured.</p>
        ) : (
          <div className="pattern-table-shell">
            <div className="pattern-list-compact">
              {contextPatterns.map((pattern, index) => (
                <div className="pattern-row-compact" key={pattern.id ?? `pattern-${index}`}>
                  <div className="pattern-row-enabled">
                    <input
                      type="checkbox"
                      checked={pattern.enabled ?? true}
                      aria-label={`Enable pattern ${index + 1}`}
                      onChange={(e) => updatePattern(index, { enabled: e.target.checked })}
                    />
                  </div>

                  <div className="pattern-row-fields">
                    <label className="pattern-mini-label">
                      <span>Before:</span>
                      <input
                        type="text"
                        value={pattern.before_text ?? ""}
                        onChange={(e) => updatePattern(index, { before_text: e.target.value })}
                        placeholder="Optional text before the player name"
                        aria-label={`Before text for pattern ${index + 1}`}
                      />
                    </label>
                    <label className="pattern-mini-label">
                      <span>After:</span>
                      <input
                        type="text"
                        value={pattern.after_text ?? ""}
                        onChange={(e) => updatePattern(index, { after_text: e.target.value })}
                        placeholder="Optional text after the player name"
                        aria-label={`After text for pattern ${index + 1}`}
                      />
                    </label>
                  </div>

                  <div className="pattern-row-actions">
                    <button
                      type="button"
                      className="danger-icon-button"
                      aria-label={`Remove pattern ${index + 1}`}
                      title="Remove pattern"
                      onClick={() => removePattern(index)}
                    >
                      <span className="material-symbols-outlined" aria-hidden="true">delete</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="context-patterns-toolbar">
              <button type="button" className="primary-action" onClick={addPattern}>
                Add pattern
              </button>
            </div>
          </div>
        )}
      </div>
    </details>
  );
}
