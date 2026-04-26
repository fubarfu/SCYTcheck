interface Props {
  spellingInfluence: number;
  temporalInfluence: number;
  disabled?: boolean;
  isRecalculating?: boolean;
  onSpellingInfluenceChange: (value: number) => void;
  onTemporalInfluenceChange: (value: number) => void;
  onRecalculate: () => void;
}

export function GroupingSettingsPanel({
  spellingInfluence,
  temporalInfluence,
  disabled = false,
  isRecalculating = false,
  onSpellingInfluenceChange,
  onTemporalInfluenceChange,
  onRecalculate,
}: Props) {
  return (
    <details className="grouping-settings-panel">
      <summary className="grouping-settings-summary">
        <span className="grouping-settings-title">Grouping settings</span>
        <span className="grouping-settings-inline-values">
          <span className="grouping-settings-chip">S {spellingInfluence}%</span>
          <span className="grouping-settings-chip">T {temporalInfluence}%</span>
        </span>
      </summary>
      <div className="grouping-settings-body">
        <label className="grouping-settings-control">
          <span>Spelling influence</span>
          <div>
            <input
              type="range"
              min={0}
              max={100}
              value={spellingInfluence}
              disabled={disabled}
              onChange={(event) => onSpellingInfluenceChange(Number(event.target.value))}
              aria-label="Spelling influence"
            />
            <strong>{spellingInfluence}%</strong>
          </div>
        </label>

        <label className="grouping-settings-control">
          <span>Temporal influence</span>
          <div>
            <input
              type="range"
              min={0}
              max={100}
              value={temporalInfluence}
              disabled={disabled}
              onChange={(event) => onTemporalInfluenceChange(Number(event.target.value))}
              aria-label="Temporal influence"
            />
            <strong>{temporalInfluence}%</strong>
          </div>
        </label>

        <p className="grouping-settings-note">
          Time proximity can boost matches but never split highly similar names by itself.
        </p>

        <div className="grouping-settings-actions">
          <button
            type="button"
            className="ghost-action"
            onClick={onRecalculate}
            disabled={disabled || isRecalculating}
          >
            {isRecalculating ? "Recalculating..." : "Recalculate Groups"}
          </button>
        </div>
      </div>
    </details>
  );
}
