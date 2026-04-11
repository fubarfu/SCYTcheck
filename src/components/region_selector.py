from __future__ import annotations

import cv2

from src.services.video_service import VideoService


class RegionSelector:
    def __init__(self, video_service: VideoService) -> None:
        self.video_service = video_service

    def select_regions(
        self,
        url: str,
        frame_time_seconds: float = 0.0,
    ) -> list[tuple[int, int, int, int]]:
        frame = self.video_service.get_frame_at_time(url, frame_time_seconds)
        selected: list[tuple[int, int, int, int]] = []

        while True:
            region = cv2.selectROI(
                "Select Region (ESC to finish)",
                frame,
                fromCenter=False,
                showCrosshair=True,
            )
            x, y, width, height = [int(value) for value in region]
            if width <= 0 or height <= 0:
                break
            selected.append((x, y, width, height))

            preview = frame.copy()
            cv2.rectangle(preview, (x, y), (x + width, y + height), (0, 255, 0), 2)
            cv2.imshow("Select Region (ESC to finish)", preview)
            if cv2.waitKey(200) == 27:
                break

        cv2.destroyAllWindows()
        return selected
