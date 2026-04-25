import { useState, useEffect, useRef } from "react";
import { AnalysisProgressPanel } from "../components/AnalysisProgressPanel";
import { AnalysisSettingsPanel } from "../components/AnalysisSettingsPanel";
import { ContextPatternsPanel } from "../components/ContextPatternsPanel";
import { clampRegionToFrame, clientPointToFramePoint } from "../utils/regionMath";

interface ScanRegion {
  x: number;
  y: number;
  width: number;
  height: number;
}

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
  context_patterns?: unknown[];
  output_folder?: string;
  scan_region?: ScanRegion;
  scan_regions?: ScanRegion[];
}

interface PreviewFrame {
  image_url: string;
  width: number;
  height: number;
  time_seconds: number;
}

type SourceType = "local_file" | "youtube_url";
type DragMode = "idle" | "draw" | "move" | "resize";
type ResizeHandle = "n" | "s" | "e" | "w" | "ne" | "nw" | "se" | "sw";

interface DragState {
  mode: DragMode;
  startX: number;
  startY: number;
  handle?: ResizeHandle;
  offsetX: number;
  offsetY: number;
  baseRegion: ScanRegion;
}

function deriveFilename(sourceType: SourceType, sourceValue: string): string {
  const now = new Date();
  const ts =
    String(now.getFullYear()) +
    String(now.getMonth() + 1).padStart(2, "0") +
    String(now.getDate()).padStart(2, "0") +
    "_" +
    String(now.getHours()).padStart(2, "0") +
    String(now.getMinutes()).padStart(2, "0") +
    String(now.getSeconds()).padStart(2, "0");

  if (!sourceValue.trim()) return `output_${ts}.csv`;
  if (sourceType === "youtube_url") {
    const match = sourceValue.match(/[?&]v=([^&]+)/);
    const id = match ? match[1] : sourceValue.slice(-11);
    return `yt_${id}_${ts}.csv`;
  }
  const base = (sourceValue.split(/[/\\]/).pop() ?? "output").replace(/\.[^.]+$/, "");
  return `${base}_${ts}.csv`;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function AnalysisPage() {
  const [sourceType, setSourceType] = useState<SourceType>("youtube_url");
  const [sourceValue, setSourceValue] = useState("");
  const [outputFolder, setOutputFolder] = useState("");
  const [outputFilename, setOutputFilename] = useState("output.csv");
  const [scanRegions, setScanRegions] = useState<ScanRegion[]>([{ x: 120, y: 40, width: 480, height: 60 }]);
  const [activeRegionIndex, setActiveRegionIndex] = useState(0);
  const [settings, setSettings] = useState<Settings>({
    video_quality: "best",
    ocr_confidence_threshold: 40,
    tolerance_value: 0.75,
    event_gap_threshold_sec: 1.0,
    gating_enabled: false,
    gating_threshold: 0.02,
    filter_non_matching: true,
    logging_enabled: false,
    context_patterns: [],
  });
  const [runId, setRunId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewFrame | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [scrubTime, setScrubTime] = useState(0);
  const [frameCursorClass, setFrameCursorClass] = useState("cursor-crosshair");
  const derivedFilenameRef = useRef(true);
  const settingsLoadedRef = useRef(false);
  const frameRef = useRef<HTMLDivElement | null>(null);
  const dragStateRef = useRef<DragState | null>(null);
  const activeRegionRef = useRef(0);

  useEffect(() => {
    activeRegionRef.current = activeRegionIndex;
  }, [activeRegionIndex]);

  useEffect(() => {
    fetch("/api/settings")
      .then((r) => r.json())
      .then((data: Settings) => {
        setSettings(data);
        if (typeof data.output_folder === "string") {
          setOutputFolder(data.output_folder);
        }
        if (Array.isArray(data.scan_regions) && data.scan_regions.length > 0) {
          setScanRegions(data.scan_regions);
          setActiveRegionIndex(0);
          activeRegionRef.current = 0;
        } else if (data.scan_region) {
          setScanRegions([data.scan_region]);
          setActiveRegionIndex(0);
          activeRegionRef.current = 0;
        }
      })
      .catch(() => {})
      .finally(() => {
        settingsLoadedRef.current = true;
      });
  }, []);

  useEffect(() => {
    if (!settingsLoadedRef.current) {
      return;
    }

    const handle = window.setTimeout(() => {
      void fetch("/api/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ output_folder: outputFolder.trim() }),
      }).catch(() => {});
    }, 250);

    return () => window.clearTimeout(handle);
  }, [outputFolder]);

  useEffect(() => {
    if (derivedFilenameRef.current) {
      setOutputFilename(deriveFilename(sourceType, sourceValue));
    }
  }, [sourceType, sourceValue]);

  const loadPreview = async (timeSeconds = 0) => {
    if (!sourceValue.trim()) {
      setPreview(null);
      return;
    }

    setPreviewLoading(true);
    setPreviewError(null);
    try {
      const resp = await fetch("/api/analysis/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_type: sourceType,
          source_value: sourceValue.trim(),
          video_quality: settings.video_quality ?? "best",
          time_seconds: timeSeconds,
        }),
      });
      const data = await resp.json() as PreviewFrame & { message?: string };
      if (!resp.ok) {
        setPreview(null);
        setPreviewError(data.message ?? "Preview unavailable");
        return;
      }
      setPreview({
        image_url: data.image_url,
        width: data.width,
        height: data.height,
        time_seconds: data.time_seconds,
      });
    } catch {
      setPreview(null);
      setPreviewError("Network error while loading preview");
    } finally {
      setPreviewLoading(false);
    }
  };

  // Auto-load on source change
  useEffect(() => {
    setPreview(null);
    setPreviewError(null);
    setScrubTime(0);

    if (sourceType !== "youtube_url" || !sourceValue.trim()) {
      return;
    }

    const handle = window.setTimeout(() => {
      void loadPreview(0);
    }, 500);
    return () => window.clearTimeout(handle);
  }, [sourceType, sourceValue, settings.video_quality]);

  // Reload preview when scrubber moves
  useEffect(() => {
    if (!preview) return;
    const handle = window.setTimeout(() => {
      void loadPreview(scrubTime);
    }, 300);
    return () => window.clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scrubTime]);

  // Drag-to-select handlers
  const setActiveRegion = (index: number) => {
    setActiveRegionIndex(index);
    activeRegionRef.current = index;
  };

  const cursorClassForHandle = (handle: ResizeHandle | null) => {
    if (!handle) {
      return "cursor-move";
    }
    if (handle === "nw" || handle === "se") {
      return "cursor-nwse";
    }
    if (handle === "ne" || handle === "sw") {
      return "cursor-nesw";
    }
    if (handle === "n" || handle === "s") {
      return "cursor-ns";
    }
    return "cursor-ew";
  };

  const addRegion = () => {
    const nextIndex = scanRegions.length;
    setScanRegions((prev) => [...prev, { x: 20, y: 20, width: 120, height: 50 }]);
    setActiveRegion(nextIndex);
  };

  const removeActiveRegion = () => {
    setScanRegions((prev) => {
      const next = prev.filter((_, index) => index !== activeRegionRef.current);
      if (next.length === 0) {
        setActiveRegion(0);
        return [];
      }
      const nextActive = Math.max(0, Math.min(activeRegionRef.current, next.length - 1));
      setActiveRegion(nextActive);
      return next;
    });
  };

  const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));

  const regionContains = (region: ScanRegion, x: number, y: number) => {
    return x >= region.x && x <= region.x + region.width && y >= region.y && y <= region.y + region.height;
  };

  const detectResizeHandle = (region: ScanRegion, x: number, y: number): ResizeHandle | null => {
    const margin = 12;
    const left = Math.abs(x - region.x) <= margin;
    const right = Math.abs(x - (region.x + region.width)) <= margin;
    const top = Math.abs(y - region.y) <= margin;
    const bottom = Math.abs(y - (region.y + region.height)) <= margin;

    if (top && left) return "nw";
    if (top && right) return "ne";
    if (bottom && left) return "sw";
    if (bottom && right) return "se";
    if (top) return "n";
    if (bottom) return "s";
    if (left) return "w";
    if (right) return "e";
    return null;
  };

  const updateRegionFromPointer = (clientX: number, clientY: number) => {
    const frame = frameRef.current;
    const drag = dragStateRef.current;
    if (!frame || !drag || !preview) return;

    const rect = frame.getBoundingClientRect();
    const point = clientPointToFramePoint(clientX, clientY, rect, preview);
    const x = point.x;
    const y = point.y;
    const regionIndex = activeRegionRef.current;

    setScanRegions((prev) => prev.map((region, index) => {
      if (index !== regionIndex) {
        return region;
      }

      if (drag.mode === "draw") {
        return clampRegionToFrame({
          x: Math.min(drag.startX, x),
          y: Math.min(drag.startY, y),
          width: Math.max(1, Math.abs(x - drag.startX)),
          height: Math.max(1, Math.abs(y - drag.startY)),
        }, preview);
      }

      if (drag.mode === "move") {
        const nx = clamp(x - drag.offsetX, 0, Math.max(0, preview.width - drag.baseRegion.width));
        const ny = clamp(y - drag.offsetY, 0, Math.max(0, preview.height - drag.baseRegion.height));
        return clampRegionToFrame({
          ...drag.baseRegion,
          x: nx,
          y: ny,
        }, preview);
      }

      if (drag.mode === "resize") {
        const base = drag.baseRegion;
        const right = base.x + base.width;
        const bottom = base.y + base.height;

        let nx = base.x;
        let ny = base.y;
        let nr = right;
        let nb = bottom;

        if (drag.handle?.includes("w")) nx = clamp(x, 0, right - 1);
        if (drag.handle?.includes("e")) nr = clamp(x, base.x + 1, preview.width);
        if (drag.handle?.includes("n")) ny = clamp(y, 0, bottom - 1);
        if (drag.handle?.includes("s")) nb = clamp(y, base.y + 1, preview.height);

        return clampRegionToFrame({
          x: nx,
          y: ny,
          width: Math.max(1, nr - nx),
          height: Math.max(1, nb - ny),
        }, preview);
      }

      return region;
    }));
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    const frame = frameRef.current;
    if (!frame || !preview) return;
    const rect = frame.getBoundingClientRect();
    const point = clientPointToFramePoint(e.clientX, e.clientY, rect, preview);

    if (scanRegions.length === 0) {
      return;
    }

    let hitIndex = -1;
    for (let i = scanRegions.length - 1; i >= 0; i -= 1) {
      if (regionContains(scanRegions[i], point.x, point.y)) {
        hitIndex = i;
        break;
      }
    }

    if (hitIndex < 0) {
      return;
    }

    const hitRegion = scanRegions[hitIndex];
    setActiveRegion(hitIndex);
    const handle = detectResizeHandle(hitRegion, point.x, point.y);

    dragStateRef.current = {
      mode: handle ? "resize" : "move",
      startX: point.x,
      startY: point.y,
      handle: handle ?? undefined,
      offsetX: point.x - hitRegion.x,
      offsetY: point.y - hitRegion.y,
      baseRegion: { ...hitRegion },
    };
    setFrameCursorClass(cursorClassForHandle(handle));

    (e.currentTarget as HTMLDivElement).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const frame = frameRef.current;
    if (!frame || !preview) return;

    if (dragStateRef.current) {
      updateRegionFromPointer(e.clientX, e.clientY);
      return;
    }

    const rect = frame.getBoundingClientRect();
    const point = clientPointToFramePoint(e.clientX, e.clientY, rect, preview);

    let hitIndex = -1;
    for (let i = scanRegions.length - 1; i >= 0; i -= 1) {
      if (regionContains(scanRegions[i], point.x, point.y)) {
        hitIndex = i;
        break;
      }
    }

    if (hitIndex < 0) {
      setFrameCursorClass("cursor-crosshair");
      return;
    }

    const hitRegion = scanRegions[hitIndex];
    const handle = detectResizeHandle(hitRegion, point.x, point.y);
    setFrameCursorClass(cursorClassForHandle(handle));
  };

  const handlePointerUp = () => {
    dragStateRef.current = null;
    setFrameCursorClass("cursor-crosshair");
  };

  const handleStart = async () => {
    setStartError(null);
    // Re-derive filename at start time so the timestamp reflects when the run begins.
    const filename = derivedFilenameRef.current
      ? deriveFilename(sourceType, sourceValue)
      : outputFilename.trim();
    if (derivedFilenameRef.current) setOutputFilename(filename);
    const payload = {
      source_type: sourceType,
      source_value: sourceValue.trim(),
      output_folder: outputFolder.trim(),
      output_filename: filename,
      scan_region: scanRegions[0],
      scan_regions: scanRegions,
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
      <div className="page-heading-row">
        <div>
        </div>
      </div>

      {!isRunning && (
        <div className="analysis-layout">
          {/* Primary column: source + preview (prominent) + output */}
          <div className="analysis-column analysis-column-primary">
            <section className="panel-card">
              <div className="panel-card-header">
                <div>
                  <h3>Select source</h3>
                </div>
              </div>
              <div className="panel-card-body">
                <div className="source-bar">
                  <select
                    className="source-bar-type"
                    value={sourceType}
                    onChange={(e) => setSourceType(e.target.value as SourceType)}
                    aria-label="Source type"
                  >
                    <option value="youtube_url">YouTube</option>
                    <option value="local_file">Local file</option>
                  </select>
                  <input
                    type="text"
                    className="source-bar-input"
                    value={sourceValue}
                    onChange={(e) => setSourceValue(e.target.value)}
                    placeholder={sourceType === "local_file" ? "C:/videos/match.mp4" : "https://youtube.com/watch?v=..."}
                    aria-label={sourceType === "local_file" ? "File path" : "YouTube URL"}
                  />
                  <button
                    type="button"
                    className="ghost-action source-bar-btn"
                    disabled={!sourceValue.trim() || previewLoading}
                    onClick={() => { void loadPreview(scrubTime); }}
                  >
                    {previewLoading ? "Loading\u2026" : preview ? "Refresh" : "Load"}
                  </button>
                </div>
              </div>
            </section>

            <section className="panel-card region-panel-card">
              <div className="panel-card-header">
                <div>
                  <h3>Define Scan regions</h3>
                </div>
                <div className="panel-card-actions region-actions">
                  <button type="button" className="ghost-action" onClick={addRegion}>
                    Add region
                  </button>
                  <button
                    type="button"
                    className="ghost-action"
                    onClick={removeActiveRegion}
                    disabled={scanRegions.length === 0}
                  >
                    Remove selected
                  </button>
                </div>
              </div>
              <div className="panel-card-body">
                {preview ? (
                  <div className="region-preview-card">
                    <div
                      ref={frameRef}
                      className={`region-preview-frame ${frameCursorClass}`}
                      onPointerDown={handlePointerDown}
                      onPointerMove={handlePointerMove}
                      onPointerUp={handlePointerUp}
                      onPointerLeave={() => {
                        handlePointerUp();
                        setFrameCursorClass("cursor-crosshair");
                      }}
                    >
                      <img src={preview.image_url} alt="Preview frame" draggable={false} />
                      <svg
                        className="region-overlay-svg"
                        viewBox={`0 0 ${preview.width} ${preview.height}`}
                        preserveAspectRatio="xMidYMid meet"
                        aria-hidden="true"
                      >
                        {scanRegions.map((region, index) => (
                          <rect
                            key={`${region.x}-${region.y}-${region.width}-${region.height}-${index}`}
                            className={`region-selection-box${index === activeRegionIndex ? " active" : ""}`}
                            x={region.x}
                            y={region.y}
                            width={region.width}
                            height={region.height}
                          />
                        ))}
                      </svg>
                    </div>
                    <div className="preview-scrubber-row">
                      <label htmlFor="preview-scrubber" className="sr-only">Seek time</label>
                      <input
                        id="preview-scrubber"
                        type="range"
                        min={0}
                        max={600}
                        step={5}
                        value={scrubTime}
                        onChange={(e) => setScrubTime(Number(e.target.value))}
                      />
                      <span className="scrub-time-label">{formatTime(scrubTime)}</span>
                    </div>
                    <div className="region-selection-meta">
                      <p className="modal-hint">Click to select. Drag inside to move. Drag border/corner to resize.</p>
                      <div className="region-coordinates">
                        {scanRegions.length > 0 ? (
                          <>
                            <span>x: {scanRegions[activeRegionIndex]?.x ?? 0}</span>
                            <span>y: {scanRegions[activeRegionIndex]?.y ?? 0}</span>
                            <span>w: {scanRegions[activeRegionIndex]?.width ?? 0}</span>
                            <span>h: {scanRegions[activeRegionIndex]?.height ?? 0}</span>
                          </>
                        ) : (
                          <span>No regions selected</span>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="empty-region-state">
                    <p>
                      {previewLoading
                        ? "Loading a preview frame\u2026"
                        : previewError ?? "Enter a video source to load a preview frame."}
                    </p>
                  </div>
                )}
              </div>
            </section>

            <details className="settings-panel" open>
              <summary>Pick where results are written</summary>
              <div className="panel-card-body form-stack">
                <label>
                  Output folder
                  <div style={{ display: "flex", gap: "6px" }}>
                    <input
                      type="text"
                      value={outputFolder}
                      onChange={(e) => setOutputFolder(e.target.value)}
                      placeholder="C:/output"
                      style={{ flex: 1 }}
                    />
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ flexShrink: 0 }}
                      onClick={async () => {
                        const params = outputFolder.trim()
                          ? `?initial_dir=${encodeURIComponent(outputFolder.trim())}`
                          : "";
                        const controller = new AbortController();
                        const timeout = setTimeout(() => controller.abort(), 180_000);
                        try {
                          const res = await fetch(`/api/fs/pick-folder${params}`, { signal: controller.signal });
                          if (res.ok) {
                            const data = await res.json();
                            if (data.path) setOutputFolder(data.path);
                          }
                        } catch {
                          // user cancelled or dialog timed out — ignore
                        } finally {
                          clearTimeout(timeout);
                        }
                      }}
                    >
                      Browse…
                    </button>
                  </div>
                </label>
                <label>
                  Output filename
                  <input
                    type="text"
                    value={outputFilename}
                    onChange={(e) => {
                      derivedFilenameRef.current = false;
                      setOutputFilename(e.target.value);
                    }}
                  />
                </label>
              </div>
            </details>
          </div>

          {/* Secondary column: settings + run */}
          <div className="analysis-column analysis-column-secondary">
            <AnalysisSettingsPanel settings={settings} onChange={setSettings} />
            <ContextPatternsPanel settings={settings} onChange={setSettings} />

            {startError && <p className="error-banner">{startError}</p>}

            <section className="panel-card action-card">
              <div className="panel-card-header">
                <div>
                  <h3>Start the analysis pass</h3>
                </div>
              </div>
              <div className="panel-card-body action-stack">
                <p className="modal-hint">Uses the selected source, output destination, and all regions shown in the preview.</p>
                <button
                  type="button"
                  className="primary-action"
                  disabled={!sourceValue.trim() || !outputFolder.trim() || !preview || scanRegions.length === 0}
                  onClick={() => { void handleStart(); }}
                >
                  Start analysis
                </button>
              </div>
            </section>
          </div>
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
    </section>
  );
}
