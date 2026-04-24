import { useState } from "react";

interface ScanRegion {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Props {
  initial: ScanRegion;
  sourceType: string;
  sourceValue: string;
  onConfirm: (region: ScanRegion) => void;
  onCancel: () => void;
}

export function RegionSelectorModal({ initial, onConfirm, onCancel }: Props) {
  const [x, setX] = useState(initial.x);
  const [y, setY] = useState(initial.y);
  const [width, setWidth] = useState(initial.width);
  const [height, setHeight] = useState(initial.height);

  const valid = width > 0 && height > 0 && x >= 0 && y >= 0;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Select scan region">
      <div className="modal-panel">
        <h3>Select scan region</h3>
        <p className="modal-hint">Define the pixel region where player names appear.</p>
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
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}
