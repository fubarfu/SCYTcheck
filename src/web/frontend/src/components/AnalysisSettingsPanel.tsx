interface Settings {
  theme?: string;
  video_quality?: string;
  ocr_confidence_threshold?: number;
  tolerance_value?: number;
  event_gap_threshold_sec?: number;
  gating_enabled?: boolean;
  gating_threshold?: number;
  filter_non_matching?: boolean;
  logging_enabled?: boolean;
}

interface Props {
  settings: Settings;
  onChange: (updated: Settings) => void;
  disabled?: boolean;
}

export function AnalysisSettingsPanel({ settings, onChange, disabled = false }: Props) {
  const update = (partial: Partial<Settings>) => onChange({ ...settings, ...partial });

  return (
    <details className="settings-panel">
      <summary>Analysis settings</summary>

      <fieldset className="settings-fieldset" disabled={disabled}>
      <div className="settings-grid">
        <label>
          Video quality
          <select
            value={settings.video_quality ?? "best"}
            onChange={(e) => update({ video_quality: e.target.value })}
          >
            <option value="best">Best</option>
            <option value="1080p">1080p</option>
            <option value="720p">720p</option>
          </select>
        </label>

        <label>
          OCR sensitivity
          <input
            type="range"
            min={0}
            max={100}
            value={settings.ocr_confidence_threshold ?? 40}
            onChange={(e) => update({ ocr_confidence_threshold: Number(e.target.value) })}
          />
          <span>{settings.ocr_confidence_threshold ?? 40}</span>
        </label>

        <label>
          Matching tolerance
          <input
            type="range"
            min={60}
            max={95}
            value={Math.round((settings.tolerance_value ?? 0.75) * 100)}
            onChange={(e) => update({ tolerance_value: Number(e.target.value) / 100 })}
          />
          <span>{(settings.tolerance_value ?? 0.75).toFixed(2)}</span>
        </label>

        <label>
          Merge gap (seconds)
          <input
            type="number"
            min={0}
            step={0.5}
            value={settings.event_gap_threshold_sec ?? 1.0}
            onChange={(e) => update({ event_gap_threshold_sec: Number(e.target.value) })}
          />
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={settings.gating_enabled ?? false}
            onChange={(e) => update({ gating_enabled: e.target.checked })}
          />
          Gating enabled
        </label>

        {(settings.gating_enabled ?? false) && (
          <label>
            Gating threshold
            <input
              type="number"
              min={0}
              max={1}
              step={0.01}
              value={settings.gating_threshold ?? 0.02}
              onChange={(e) => update({ gating_threshold: Number(e.target.value) })}
            />
          </label>
        )}

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={settings.filter_non_matching ?? true}
            onChange={(e) => update({ filter_non_matching: e.target.checked })}
          />
          Filter non-matching results
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={settings.logging_enabled ?? false}
            onChange={(e) => update({ logging_enabled: e.target.checked })}
          />
          Detailed sidecar log
        </label>
      </div>
      </fieldset>
    </details>
  );
}
