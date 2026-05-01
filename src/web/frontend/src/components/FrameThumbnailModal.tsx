interface Props {
  candidateId: string;
  thumbnailUrl: string | null;
  metadata?: {
    timestamp?: string;
    sourceType?: string;
  };
  onClose: () => void;
}

export function FrameThumbnailModal({ candidateId, thumbnailUrl, metadata, onClose }: Props) {
  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Frame thumbnail">
      <div className="modal-panel thumbnail-modal">
        <h3>Candidate frame: {candidateId}</h3>
        {thumbnailUrl ? (
          <img src={thumbnailUrl} alt={`Frame for ${candidateId}`} className="thumbnail-image" />
        ) : (
          <p>No thumbnail available for this candidate.</p>
        )}
        <div className="thumb-meta">
          <span>Timestamp: {metadata?.timestamp ?? "-"}s</span>
          <span>Source: {metadata?.sourceType ?? "-"}</span>
        </div>
        <div className="modal-actions">
          <button type="button" className="primary-action" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
