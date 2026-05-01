type ProgressWindowProps = {
  visible: boolean;
  statusText: string;
  progressPercent?: number;
  projectInfo?: string;
  onClose?: () => void;
};

export function ProgressWindow({
  visible,
  statusText,
  progressPercent = 0,
  projectInfo,
  onClose,
}: ProgressWindowProps) {
  if (!visible) {
    return null;
  }

  const boundedPercent = Math.max(0, Math.min(100, Math.round(progressPercent)));

  return (
    <div className="progress-window" role="status" aria-live="polite">
      <div className="progress-window__panel">
        <h3>Analysis Running</h3>
        <p className="progress-window__status">{statusText || "Processing video frames..."}</p>
        <p className="progress-window__hint">This can take a minute for longer videos. Review will open automatically when ready.</p>
        <div className="progress-window__bar" aria-hidden="true">
          <div className="progress-window__bar-fill" style={{ width: `${boundedPercent}%` }} />
        </div>
        <p className="progress-window__percent">{boundedPercent}% complete</p>
        {projectInfo ? <p className="progress-window__meta">Project state: {projectInfo}</p> : null}
        {onClose ? (
          <button type="button" className="progress-window__close" onClick={onClose}>
            Hide
          </button>
        ) : null}
      </div>
    </div>
  );
}
