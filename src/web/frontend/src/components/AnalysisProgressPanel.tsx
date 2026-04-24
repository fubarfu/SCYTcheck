import { useEffect, useState, useCallback } from "react";

interface ProgressState {
  run_id: string;
  status: string;
  stage_label: string;
  frames_processed: number;
  frames_estimated_total: number;
}

interface ResultState {
  run_id: string;
  status: string;
  csv_path: string | null;
  partial: boolean;
}

interface Props {
  runId: string;
  onCompleted: (csvPath: string) => void;
  onStopped: () => void;
}

export function AnalysisProgressPanel({ runId, onCompleted, onStopped }: Props) {
  const [progress, setProgress] = useState<ProgressState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stopping, setStopping] = useState(false);

  const poll = useCallback(async () => {
    try {
      const resp = await fetch(`/api/analysis/progress/${runId}`);
      if (!resp.ok) {
        setError("Failed to fetch progress");
        return;
      }
      const data = (await resp.json()) as ProgressState;
      setProgress(data);

      if (data.status === "completed" || data.status === "failed") {
        const resultResp = await fetch(`/api/analysis/result/${runId}`);
        const result = (await resultResp.json()) as ResultState;
        if (result.status === "completed" && result.csv_path) {
          onCompleted(result.csv_path);
        } else if (result.status === "failed") {
          setError("Analysis failed. Check logs for details.");
        }
      }
    } catch {
      setError("Network error while polling progress");
    }
  }, [runId, onCompleted]);

  useEffect(() => {
    const interval = setInterval(() => { void poll(); }, 1000);
    void poll();
    return () => clearInterval(interval);
  }, [poll]);

  const handleStop = async () => {
    setStopping(true);
    try {
      await fetch(`/api/analysis/stop/${runId}`, { method: "POST" });
    } catch {
      // ignore stop request errors
    }
    setTimeout(onStopped, 1500);
  };

  const handleRetry = () => {
    setError(null);
    setStopping(false);
    void poll();
  };

  const pct =
    progress && progress.frames_estimated_total > 0
      ? Math.min(100, Math.round((progress.frames_processed / progress.frames_estimated_total) * 100))
      : null;

  return (
    <div className="progress-panel" aria-live="polite">
      <h3>Analysis in progress</h3>

      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <button type="button" onClick={handleRetry}>Retry</button>
          <button type="button" onClick={onStopped}>Dismiss</button>
        </div>
      )}

      {progress && !error && (
        <>
          <p className="stage-label">{progress.stage_label || "Processing..."}</p>
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill"
              style={{ width: pct !== null ? `${pct}%` : "0%" }}
              aria-valuenow={pct ?? 0}
              aria-valuemin={0}
              aria-valuemax={100}
              role="progressbar"
            />
          </div>
          {pct !== null && (
            <p className="progress-pct">{pct}% ({progress.frames_processed} / {progress.frames_estimated_total} frames)</p>
          )}
        </>
      )}

      <button
        type="button"
        className="stop-action"
        disabled={stopping}
        onClick={() => { void handleStop(); }}
      >
        {stopping ? "Stopping..." : "Stop"}
      </button>
    </div>
  );
}
