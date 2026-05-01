import { useMemo, useRef, useState } from "react";

interface ScanRegion {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Props {
  initial: ScanRegion;
  previewUrl: string;
  previewWidth: number;
  previewHeight: number;
  onConfirm: (region: ScanRegion) => void;
  onCancel: () => void;
}

export function RegionSelectorModal({
  initial,
  previewUrl,
  previewWidth,
  previewHeight,
  onConfirm,
  onCancel,
}: Props) {
  const [x, setX] = useState(initial.x);
  const [y, setY] = useState(initial.y);
  const [width, setWidth] = useState(initial.width);
  const [height, setHeight] = useState(initial.height);
  const frameRef = useRef<HTMLDivElement | null>(null);
  const dragStartRef = useRef<{ x: number; y: number } | null>(null);

  const valid = width > 0 && height > 0 && x >= 0 && y >= 0;
  const overlayStyle = useMemo(() => ({
    left: `${(x / previewWidth) * 100}%`,
    top: `${(y / previewHeight) * 100}%`,
    width: `${(width / previewWidth) * 100}%`,
    height: `${(height / previewHeight) * 100}%`,
  }), [height, previewHeight, previewWidth, width, x, y]);

  const updateFromPointer = (clientX: number, clientY: number) => {
    const frame = frameRef.current;
    const start = dragStartRef.current;
    if (!frame || !start) {
      return;
    }
    const rect = frame.getBoundingClientRect();
    const clampX = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const clampY = Math.max(0, Math.min(clientY - rect.top, rect.height));
    const endX = Math.round((clampX / rect.width) * previewWidth);
    const endY = Math.round((clampY / rect.height) * previewHeight);
    setX(Math.min(start.x, endX));
    setY(Math.min(start.y, endY));
    setWidth(Math.max(1, Math.abs(endX - start.x)));
    setHeight(Math.max(1, Math.abs(endY - start.y)));
  };

  const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    const frame = frameRef.current;
    if (!frame) {
      return;
    }
    const rect = frame.getBoundingClientRect();
    const startX = Math.round(((event.clientX - rect.left) / rect.width) * previewWidth);
    const startY = Math.round(((event.clientY - rect.top) / rect.height) * previewHeight);
    dragStartRef.current = {
      x: Math.max(0, Math.min(previewWidth, startX)),
      y: Math.max(0, Math.min(previewHeight, startY)),
    };
    updateFromPointer(event.clientX, event.clientY);
  };

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!dragStartRef.current) {
      return;
    }
    updateFromPointer(event.clientX, event.clientY);
  };

  const handlePointerUp = () => {
    dragStartRef.current = null;
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Select scan region">
      <div className="modal-panel region-modal-panel">
        <div className="modal-header-row">
          <div>
            <h3>Select scan region</h3>
            <p className="modal-hint">Drag on the preview frame to define the area to scan for player names.</p>
          </div>
          <button type="button" className="ghost-action" onClick={onCancel}>Close</button>
        </div>
        <div
          ref={frameRef}
          className="region-preview-frame"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
        >
          <img src={previewUrl} alt="Preview frame for region selection" />
          <div className="region-preview-scrim" />
          <div className="region-selection-box" style={overlayStyle} />
        </div>
        <div className="region-selection-meta">
          <p className="modal-hint">Drag to redraw the selection. The coordinate fields remain editable for fine adjustment.</p>
          <div className="region-coordinates">
            <span>x: {x}</span>
            <span>y: {y}</span>
            <span>w: {width}</span>
            <span>h: {height}</span>
          </div>
        </div>
        <div className="region-fields">
          <label>
            X
            <input type="number" value={x} min={0} onChange={(e) => setX(Number(e.target.value))} />
          </label>
          <label>
            Y
            <input type="number" value={y} min={0} onChange={(e) => setY(Number(e.target.value))} />
          </label>
          <label>
            Width
            <input type="number" value={width} min={1} onChange={(e) => setWidth(Number(e.target.value))} />
          </label>
          <label>
            Height
            <input type="number" value={height} min={1} onChange={(e) => setHeight(Number(e.target.value))} />
          </label>
        </div>
        <div className="modal-actions">
          <button type="button" onClick={onCancel}>Cancel</button>
          <button
            type="button"
            className="primary-action"
            disabled={!valid}
            onClick={() => onConfirm({ x, y, width, height })}
          >
            Confirm region
          </button>
        </div>
      </div>
    </div>
  );
}
