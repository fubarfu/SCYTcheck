from __future__ import annotations

import logging
from unittest.mock import patch

import numpy as np

from src.services.video_service import VideoService


class _LoggingCapture:
    def __init__(self) -> None:
        self.current = 0

    def isOpened(self) -> bool:
        return True

    def get(self, prop: int) -> float:
        if prop == 5:
            return 30.0
        return 0.0

    def set(self, prop: int, value: float) -> bool:
        if prop == 1:
            self.current = int(value)
        return True

    def read(self):
        if self.current > 60:
            return False, None
        frame = np.zeros((4, 4, 3), dtype=np.uint8)
        self.current += 1
        return True, frame

    def release(self) -> None:
        return None


def test_logging_contract_emits_init_event_without_repeated_random_seek_events(caplog) -> None:
    service = VideoService()
    cap = _LoggingCapture()

    with (
        patch.object(service, "_extract_media_url", return_value=("stream", {})),
        patch("src.services.video_service.cv2.VideoCapture", return_value=cap),
        caplog.at_level(logging.DEBUG),
    ):
        list(
            service.iterate_frames_with_timestamps(
                "https://youtube.com/watch?v=logging",
                start_time=0.0,
                end_time=2.0,
                fps=1,
            )
        )

    records = [r for r in caplog.records if r.message == "video_iteration"]
    assert records
    payloads = [record.__dict__.get("video_iteration", {}) for record in records]
    init_events = [p for p in payloads if p.get("event_type") == "init"]
    assert len(init_events) == 1
