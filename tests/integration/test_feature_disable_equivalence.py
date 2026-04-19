from __future__ import annotations

import numpy as np

from src.services.analysis_service import AnalysisService


class _EquivalenceVideoService:
    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        del url, start_time, end_time, fps, quality
        for idx in range(3):
            yield float(idx), np.zeros((10, 10, 3), dtype=np.uint8)


class _EquivalenceOCRService:
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


def test_default_tolerance_075_preserves_strict_behavior_equivalence() -> None:
    service = AnalysisService(
        video_service=_EquivalenceVideoService(),
        ocr_service=_EquivalenceOCRService(),
    )

    baseline = service.analyze(
        url="https://youtube.com/watch?v=equiv",
        regions=[(0, 0, 5, 5)],
        start_time=0.0,
        end_time=2.0,
        fps=1,
        tolerance_value=0.75,
        gating_enabled=False,
    )
    candidate = service.analyze(
        url="https://youtube.com/watch?v=equiv",
        regions=[(0, 0, 5, 5)],
        start_time=0.0,
        end_time=2.0,
        fps=1,
        tolerance_value=0.75,
        gating_enabled=False,
    )

    candidate_names = [summary.player_name for summary in candidate.player_summaries]
    baseline_names = [summary.player_name for summary in baseline.player_summaries]

    assert candidate_names == baseline_names
    assert len(candidate.detections) == len(baseline.detections)
