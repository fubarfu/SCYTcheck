from __future__ import annotations

import time

import numpy as np

from src.services.analysis_service import AnalysisService


class _MetricsVideoService:
    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        del url, start_time, end_time, fps, quality
        frame = np.zeros((20, 20, 3), dtype=np.uint8)
        for idx in range(30):
            yield float(idx), frame


class _MetricsOCRService:
    def detect_text(self, frame, region):
        del frame, region
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


def test_baseline_metrics_runtime_and_throughput_are_recordable() -> None:
    service = AnalysisService(
        video_service=_MetricsVideoService(),
        ocr_service=_MetricsOCRService(),
    )

    started = time.perf_counter()
    analysis = service.analyze(
        url="https://youtube.com/watch?v=baseline",
        regions=[(0, 0, 10, 10)],
        start_time=0.0,
        end_time=29.0,
        fps=1,
        gating_enabled=False,
    )
    runtime = time.perf_counter() - started
    throughput = 30 / runtime if runtime > 0 else 0.0

    assert runtime > 0.0
    assert throughput > 0.0
    assert analysis.player_summaries
