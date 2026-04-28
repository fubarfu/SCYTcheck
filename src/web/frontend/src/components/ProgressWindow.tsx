type ProgressWindowProps = {
  visible: boolean;
  statusText: string;
  onClose?: () => void;
};

export function ProgressWindow({ visible, statusText, onClose }: ProgressWindowProps) {
  if (!visible) {
    return null;
  }

  return (
    <div className="progress-window" role="status" aria-live="polite">
      <div className="progress-window__panel">
        <h3>Analysis In Progress</h3>
        <p>{statusText || "Preparing analysis..."}</p>
        <div className="progress-window__bar" aria-hidden="true">
          <div className="progress-window__bar-fill" />
        </div>
        {onClose ? (
          <button type="button" className="progress-window__close" onClick={onClose}>
            Hide
          </button>
        ) : null}
      </div>
    </div>
  );
}
