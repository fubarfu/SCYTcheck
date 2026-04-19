from __future__ import annotations

import numpy as np

from src.services.analysis_service import AnalysisService


class _MixedVideoService:
    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        del url, start_time, end_time, fps, quality
        base = np.zeros((20, 20, 3), dtype=np.uint8)
        for idx in range(40):
            frame = base.copy()
            if idx % 10 == 0:
                frame[0:5, 0:5] = 200
            yield float(idx), frame


class _DeterministicOCRService:
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


def test_us3_gated_and_ungated_detection_variance_is_within_one_percent() -> None:
    service = AnalysisService(
        video_service=_MixedVideoService(),
        ocr_service=_DeterministicOCRService(),
    )
    regions = [(0, 0, 10, 10)]

    ungated = service.analyze(
        url="https://youtube.com/watch?v=accuracy",
        regions=regions,
        start_time=0.0,
        end_time=39.0,
        fps=1,
        gating_enabled=False,
    )
    gated = service.analyze(
        url="https://youtube.com/watch?v=accuracy",
        regions=regions,
        start_time=0.0,
        end_time=39.0,
        fps=1,
        gating_enabled=True,
        gating_threshold=0.02,
    )

    baseline = len(ungated.detections)
    diff = abs(len(ungated.detections) - len(gated.detections))
    variance_pct = (diff / baseline) * 100 if baseline else 0.0

    assert variance_pct <= 1.0
