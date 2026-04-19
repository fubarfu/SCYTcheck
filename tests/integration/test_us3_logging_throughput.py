from __future__ import annotations

import time

import numpy as np

from src.services.analysis_service import AnalysisService


class _VideoServiceForThroughput:
    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        del url, start_time, end_time, fps, quality
        frame = np.zeros((16, 16, 3), dtype=np.uint8)
        for idx in range(50):
            yield float(idx), frame


class _OCRServiceForThroughput:
    def detect_text(self, frame, region):
        del frame, region
        return ["raw"]

    def detect_text_with_diagnostics(self, frame, region):
        del frame, region
        return ["raw"], [
            {
                "raw_string": "raw",
                "accepted": False,
                "rejection_reason": "low_confidence",
            }
        ]

    def evaluate_lines(
        self,
        lines,
        patterns=None,
        filter_non_matching=False,
        tolerance_threshold=0.75,
    ):
        del lines, patterns, filter_non_matching, tolerance_threshold
        # Simulate additional per-frame work when detailed logging path is used.
        time.sleep(0.001)
        return [
            {
                "raw_string": "raw",
                "accepted": False,
                "rejection_reason": "no_pattern_match",
                "extracted_name": "",
                "matched_pattern": None,
            }
        ]

    def extract_candidates(
        self,
        lines,
        patterns=None,
        filter_non_matching=False,
        tolerance_threshold=0.75,
    ):
        del lines, patterns, filter_non_matching, tolerance_threshold
        return [("Alice", "p")]


def test_us3_logging_disabled_throughput_is_at_least_15_percent_higher() -> None:
    service = AnalysisService(
        video_service=_VideoServiceForThroughput(),
        ocr_service=_OCRServiceForThroughput(),
    )
    regions = [(0, 0, 8, 8)]

    started = time.perf_counter()
    service.analyze(
        url="https://youtube.com/watch?v=logging",
        regions=regions,
        start_time=0.0,
        end_time=49.0,
        fps=1,
        logging_enabled=True,
        gating_enabled=False,
    )
    logging_on_seconds = time.perf_counter() - started

    started = time.perf_counter()
    service.analyze(
        url="https://youtube.com/watch?v=logging",
        regions=regions,
        start_time=0.0,
        end_time=49.0,
        fps=1,
        logging_enabled=False,
        gating_enabled=False,
    )
    logging_off_seconds = time.perf_counter() - started

    on_throughput = 50 / logging_on_seconds
    off_throughput = 50 / logging_off_seconds

    assert off_throughput >= on_throughput * 1.15
