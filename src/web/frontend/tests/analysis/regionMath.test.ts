import { describe, expect, it } from "vitest";

import {
  clampRegionToFrame,
  clientPointToFramePoint,
  getContainedImageRect,
} from "../../src/utils/regionMath";

describe("regionMath", () => {
  it("maps pointer coordinates against the contained image area, not the full letterboxed frame", () => {
    const rect = { left: 0, top: 0, width: 400, height: 225 };
    const frame = { width: 400, height: 300 };

    const imageRect = getContainedImageRect(rect, frame);
    expect(imageRect).toEqual({ left: 50, top: 0, width: 300, height: 225 });

    expect(clientPointToFramePoint(50, 0, rect, frame)).toEqual({ x: 0, y: 0 });
    expect(clientPointToFramePoint(350, 225, rect, frame)).toEqual({ x: 400, y: 300 });
    expect(clientPointToFramePoint(200, 112.5, rect, frame)).toEqual({ x: 200, y: 150 });
  });

  it("clamps regions so they remain fully inside the frame", () => {
    expect(
      clampRegionToFrame({ x: -20, y: 10, width: 500, height: 1000 }, { width: 320, height: 180 }),
    ).toEqual({ x: 0, y: 10, width: 320, height: 170 });
  });
});