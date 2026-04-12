from __future__ import annotations

import logging
from unittest.mock import patch

import numpy as np

from src.services.video_service import VideoService


class _FallbackCapture:
    def __init__(self) -> None:
        self.current = 0
        self.failed_once = False

    def isOpened(self) -> bool:
        return True

    def get(self, prop: int) -> float:
        if prop == 5:
            return 10.0
        return 0.0

    def set(self, prop: int, value: float) -> bool:
        if prop == 1:
            self.current = int(value)
        return True

    def read(self):
        if self.current >= 10 and not self.failed_once:
            self.failed_once = True
            return False, None
        frame = np.zeros((3, 3, 3), dtype=np.uint8)
        self.current += 1
        return True, frame

    def release(self) -> None:
        return None


def test_decode_error_fallback_preserves_sampled_timestamp_count() -> None:
    service = VideoService()
    cap = _FallbackCapture()

    with (
        patch.object(service, "_extract_media_url", return_value=("stream", {})),
        patch("src.services.video_service.cv2.VideoCapture", return_value=cap),
    ):
        baseline_indexes = service._build_target_frame_indexes(10, 30, 10)
        items = list(
            service.iterate_frames_with_timestamps(
                "https://youtube.com/watch?v=fallback",
                start_time=1.0,
                end_time=3.0,
                fps=1,
            )
        )

    assert len(items) == len(baseline_indexes)


def test_fallback_reason_categories_are_guarded() -> None:
    service = VideoService()
    assert service._should_fallback("decode_error", "x") is True
    assert service._should_fallback("performance_probe", "x") is True
    assert service._should_fallback("unexpected", "x") is False


def test_fallback_telemetry_includes_reason_and_source_identifier(caplog) -> None:
    service = VideoService()
    cap = _FallbackCapture()

    with (
        patch.object(service, "_extract_media_url", return_value=("stream", {})),
        patch("src.services.video_service.cv2.VideoCapture", return_value=cap),
        caplog.at_level(logging.DEBUG),
    ):
        list(
            service.iterate_frames_with_timestamps(
                "https://youtube.com/watch?v=fallback",
                start_time=1.0,
                end_time=3.0,
                fps=1,
            )
        )

    payloads = [record.__dict__.get("video_iteration", {}) for record in caplog.records]
    fallback_events = [p for p in payloads if p.get("event_type") == "fallback"]
    assert fallback_events
    assert fallback_events[0]["reason"] in {"decode_error", "performance_probe"}
    assert fallback_events[0]["source_id"] == "https://youtube.com/watch?v=fallback|best"
