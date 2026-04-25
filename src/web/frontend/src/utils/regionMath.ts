export interface FrameSize {
  width: number;
  height: number;
}

export interface ClientRectLike {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface FramePoint {
  x: number;
  y: number;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function getContainedImageRect(rect: ClientRectLike, frame: FrameSize): ClientRectLike {
  if (rect.width <= 0 || rect.height <= 0 || frame.width <= 0 || frame.height <= 0) {
    return { left: rect.left, top: rect.top, width: rect.width, height: rect.height };
  }

  const containerAspect = rect.width / rect.height;
  const frameAspect = frame.width / frame.height;

  if (containerAspect > frameAspect) {
    const height = rect.height;
    const width = height * frameAspect;
    const left = rect.left + (rect.width - width) / 2;
    return { left, top: rect.top, width, height };
  }

  const width = rect.width;
  const height = width / frameAspect;
  const top = rect.top + (rect.height - height) / 2;
  return { left: rect.left, top, width, height };
}

export function clientPointToFramePoint(
  clientX: number,
  clientY: number,
  rect: ClientRectLike,
  frame: FrameSize,
): FramePoint {
  const imageRect = getContainedImageRect(rect, frame);
  const px = clamp(clientX - imageRect.left, 0, imageRect.width);
  const py = clamp(clientY - imageRect.top, 0, imageRect.height);

  return {
    x: clamp(Math.round((px / imageRect.width) * frame.width), 0, frame.width),
    y: clamp(Math.round((py / imageRect.height) * frame.height), 0, frame.height),
  };
}

export function clampRegionToFrame(
  region: { x: number; y: number; width: number; height: number },
  frame: FrameSize,
): { x: number; y: number; width: number; height: number } {
  const x = clamp(Math.round(region.x), 0, Math.max(0, frame.width - 1));
  const y = clamp(Math.round(region.y), 0, Math.max(0, frame.height - 1));
  const maxWidth = Math.max(1, frame.width - x);
  const maxHeight = Math.max(1, frame.height - y);
  const width = clamp(Math.round(region.width), 1, maxWidth);
  const height = clamp(Math.round(region.height), 1, maxHeight);
  return { x, y, width, height };
}