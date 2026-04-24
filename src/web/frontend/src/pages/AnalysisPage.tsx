import { useState, useEffect, useRef } from "react";
import { RegionSelectorModal } from "../components/RegionSelectorModal";
import { AnalysisProgressPanel } from "../components/AnalysisProgressPanel";
import { AnalysisSettingsPanel } from "../components/AnalysisSettingsPanel";

interface ScanRegion {
  x: number;
  y: number;
  width: number;
  height: number;
}

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
  scan_region?: ScanRegion;
}

type SourceType = "local_file" | "youtube_url";

function deriveFilename(sourceType: SourceType, sourceValue: string): string {
  if (!sourceValue.trim()) return "output.csv";
  if (sourceType === "youtube_url") {
    const match = sourceValue.match(/[?&]v=([^&]+)/);
    const id = match ? match[1] : sourceValue.slice(-11);
    return `yt_${id}.csv`;
  }
  const base = sourceValue.split(/[/\\]/).pop() ?? "output";
  return base.replace(/\.[^.]+$/, "") + ".csv";
}

export function AnalysisPage() {
  const [sourceType, setSourceType] = useState<SourceType>("local_file");
  const [sourceValue, setSourceValue] = useState("");
  const [outputFolder, setOutputFolder] = useState("");
  const [outputFilename, setOutputFilename] = useState("output.csv");
  const [scanRegion, setScanRegion] = useState<ScanRegion>({ x: 120, y: 40, width: 480, height: 60 });
  const [settings, setSettings] = useState<Settings>({});
  const [showRegionModal, setShowRegionModal] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const derivedFilenameRef = useRef(true);

  useEffect(() => {
    fetch("/api/settings")
      .then((r) => r.json())
      .then((data: Settings) => {
        setSettings(data);
        if (data.scan_region) setScanRegion(data.scan_region);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (derivedFilenameRef.current) {
      setOutputFilename(deriveFilename(sourceType, sourceValue));
    }
  }, [sourceType, sourceValue]);

  const handleStart = async () => {
    setStartError(null);
    const payload = {
      source_type: sourceType,
      source_value: sourceValue.trim(),
      output_folder: outputFolder.trim(),
      output_filename: outputFilename.trim(),
      scan_region: scanRegion,
      ...settings,
    };
    const resp = await fetch("/api/analysis/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (resp.status === 202) {
      const data = await resp.json() as { run_id: string };
      setRunId(data.run_id);
      setIsRunning(true);
    } else {
      const err = await resp.json().catch(() => ({ message: "Unknown error" })) as { message?: string };
      setStartError(err.message ?? "Start failed");
    }
  };

  return (
    <section className="page-panel">
      <h2>Analysis</h2>

      {!isRunning && (
        <div className="analysis-form">
          <label>
            Source type
            <select value={sourceType} onChange={(e) => setSourceType(e.target.value as SourceType)}>
              <option value="local_file">Local file</option>
              <option value="youtube_url">YouTube URL</option>
            </select>
          </label>
          <label>
            {sourceType === "local_file" ? "File path" : "YouTube URL"}
            <input
              type="text"
              value={sourceValue}
              onChange={(e) => setSourceValue(e.target.value)}
              placeholder={sourceType === "local_file" ? "C:/videos/match.mp4" : "https://youtube.com/watch?v=..."}
            />
          </label>
          <label>
            Output folder
            <input
              type="text"
              value={outputFolder}
              onChange={(e) => setOutputFolder(e.target.value)}
              placeholder="C:/output"
            />
          </label>
          <label>
            Output filename (auto-generated)
            <input
              type="text"
              value={outputFilename}
              onChange={(e) => {
                derivedFilenameRef.current = false;
                setOutputFilename(e.target.value);
              }}
            />
          </label>

          <div className="region-row">
            <span>
              Scan region: {scanRegion.x},{scanRegion.y} {scanRegion.width}x{scanRegion.height}
            </span>
            <button type="button" onClick={() => setShowRegionModal(true)}>
              Select region...
            </button>
          </div>

          <AnalysisSettingsPanel settings={settings} onChange={setSettings} />

          {startError && <p className="error-banner">{startError}</p>}

          <button
            type="button"
            className="primary-action"
            disabled={!sourceValue.trim() || !outputFolder.trim()}
            onClick={() => { void handleStart(); }}
          >
            Start analysis
          </button>
        </div>
      )}

      {isRunning && runId && (
        <AnalysisProgressPanel
          runId={runId}
          onCompleted={(csvPath) => {
            setIsRunning(false);
            setRunId(null);
            window.dispatchEvent(new CustomEvent("scyt:open-review", { detail: { csvPath } }));
          }}
          onStopped={() => {
            setIsRunning(false);
            setRunId(null);
          }}
        />
      )}

      {showRegionModal && (
        <RegionSelectorModal
          initial={scanRegion}
          sourceType={sourceType}
          sourceValue={sourceValue}
          onConfirm={(region) => {
            setScanRegion(region);
            setShowRegionModal(false);
          }}
          onCancel={() => setShowRegionModal(false)}
        />
      )}
    </section>
  );
}
