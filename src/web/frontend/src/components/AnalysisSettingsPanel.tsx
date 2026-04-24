interface Settings {
  theme?: string;
  video_quality?: string;
  ocr_sensitivity?: number;
  matching_tolerance?: number;
  event_merge_gap_seconds?: number;
  gating_enabled?: boolean;
  gating_threshold?: number;
  filter_non_matching?: boolean;
  detailed_sidecar_log?: boolean;
  context_patterns?: unknown[];
}

interface Props {
  settings: Settings;
  onChange: (updated: Settings) => void;
}

export function AnalysisSettingsPanel({ settings, onChange }: Props) {
  const update = (partial: Partial<Settings>) => onChange({ ...settings, ...partial });

  return (
    <details className="settings-panel">
      <summary>Analysis settings</summary>

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
            value={settings.ocr_sensitivity ?? 70}
            onChange={(e) => update({ ocr_sensitivity: Number(e.target.value) })}
          />
          <span>{settings.ocr_sensitivity ?? 70}</span>
        </label>

        <label>
          Matching tolerance
          <input
            type="range"
            min={0}
            max={100}
            value={settings.matching_tolerance ?? 80}
            onChange={(e) => update({ matching_tolerance: Number(e.target.value) })}
          />
          <span>{settings.matching_tolerance ?? 80}</span>
        </label>

        <label>
          Merge gap (seconds)
          <input
            type="number"
            min={0}
            step={0.5}
            value={settings.event_merge_gap_seconds ?? 2.0}
            onChange={(e) => update({ event_merge_gap_seconds: Number(e.target.value) })}
          />
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={settings.gating_enabled ?? true}
            onChange={(e) => update({ gating_enabled: e.target.checked })}
          />
          Gating enabled
        </label>

        {(settings.gating_enabled ?? true) && (
          <label>
            Gating threshold
            <input
              type="number"
              min={1}
              value={settings.gating_threshold ?? 12}
              onChange={(e) => update({ gating_threshold: Number(e.target.value) })}
            />
          </label>
        )}

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={settings.filter_non_matching ?? false}
            onChange={(e) => update({ filter_non_matching: e.target.checked })}
          />
          Filter non-matching results
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={settings.detailed_sidecar_log ?? false}
            onChange={(e) => update({ detailed_sidecar_log: e.target.checked })}
          />
          Detailed sidecar log
        </label>
      </div>
    </details>
  );
}
