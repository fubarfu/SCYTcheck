from __future__ import annotations

from unittest.mock import patch

import numpy as np

from src.services.video_service import VideoService


class _NetworkLikeCapture:
    def __init__(self) -> None:
        self.current = 0
        self.set_calls: list[tuple[int, int]] = []

    def isOpened(self) -> bool:
        return True

    def get(self, prop: int) -> float:
        if prop == 5:
            return 30.0
        return 0.0

    def set(self, prop: int, value: float) -> bool:
        self.set_calls.append((prop, int(value)))
        if prop == 1:
            self.current = int(value)
        return True

    def read(self):
        if self.current > 120:
            return False, None
        frame = np.zeros((8, 8, 3), dtype=np.uint8)
        self.current += 1
        return True, frame

    def release(self) -> None:
        return None


def test_network_stream_iteration_has_single_init_seek_and_no_reseek_loop() -> None:
    service = VideoService()
    cap = _NetworkLikeCapture()

    with (
        patch.object(service, "_extract_media_url", return_value=("net-stream", {})),
        patch("src.services.video_service.cv2.VideoCapture", return_value=cap),
    ):
        items = list(
            service.iterate_frames_with_timestamps(
                "https://youtube.com/watch?v=stream",
                start_time=0.0,
                end_time=3.0,
                fps=1,
            )
        )

    assert items
    seek_calls = [c for c in cap.set_calls if c[0] == 1]
    assert len(seek_calls) == 1
