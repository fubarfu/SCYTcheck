from __future__ import annotations

import time

import numpy as np

from src.services.analysis_service import AnalysisService


class _StaticVideoService:
    def __init__(self, frame_count: int) -> None:
        self._frame_count = frame_count

    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        del url, start_time, end_time, fps, quality
        frame = np.zeros((24, 24, 3), dtype=np.uint8)
        for idx in range(self._frame_count):
            yield float(idx), frame


class _SlowOCRService:
    def detect_text(self, frame, region):
        del frame, region
        time.sleep(0.001)
        return ["Player: Alice"]

    def extract_candidates(
        self,
        lines,
        patterns=None,
        filter_non_matching=False,
        tolerance_threshold=0.75,
    ):
        del lines, patterns, filter_non_matching, tolerance_threshold
        return [("Alice", "p")]


def test_us3_gating_enabled_is_at_least_30_percent_faster_on_static_frames() -> None:
    video = _StaticVideoService(frame_count=60)
    ocr = _SlowOCRService()
    service = AnalysisService(video_service=video, ocr_service=ocr)
    regions = [(0, 0, 12, 12)]

    started = time.perf_counter()
    service.analyze(
        url="https://youtube.com/watch?v=static",
        regions=regions,
        start_time=0.0,
        end_time=59.0,
        fps=1,
        gating_enabled=False,
    )
    ungated = time.perf_counter() - started

    started = time.perf_counter()
    service.analyze(
        url="https://youtube.com/watch?v=static",
        regions=regions,
        start_time=0.0,
        end_time=59.0,
        fps=1,
        gating_enabled=True,
        gating_threshold=0.02,
    )
    gated = time.perf_counter() - started

    assert gated < ungated * 0.70
