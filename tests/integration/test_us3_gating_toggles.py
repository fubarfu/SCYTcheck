from __future__ import annotations

from unittest.mock import Mock

import numpy as np

from src.services.analysis_service import AnalysisService
from src.services.video_service import VideoService


class _OCRCounterStub:
    def __init__(self) -> None:
        self.calls = 0

    def detect_text(self, frame, region):
        del frame, region
        self.calls += 1
        return ["Player: Alice"]

    def extract_candidates(
        self,
        lines,
        patterns=None,
        filter_non_matching=False,
        tolerance_threshold=0.75,
    ):
        del lines, patterns, filter_non_matching, tolerance_threshold
        return [("Alice", "pattern")]


def test_us3_gating_disabled_executes_all_pairs_and_skips_none() -> None:
    video_service = Mock(spec=VideoService)
    video_service.iterate_frames_with_timestamps.return_value = [
        (0.0, np.zeros((10, 10, 3), dtype=np.uint8)),
        (1.0, np.zeros((10, 10, 3), dtype=np.uint8)),
        (2.0, np.zeros((10, 10, 3), dtype=np.uint8)),
    ]

    ocr = _OCRCounterStub()
    service = AnalysisService(video_service=video_service, ocr_service=ocr)

    analysis = service.analyze(
        url="https://youtube.com/watch?v=gatingtoggle",
        regions=[(0, 0, 5, 5), (5, 5, 5, 5)],
        start_time=0.0,
        end_time=2.0,
        fps=1,
        gating_enabled=False,
        gating_threshold=0.02,
    )

    assert analysis.gating_stats is not None
    assert analysis.gating_stats.total_frame_region_pairs == 6
    assert analysis.gating_stats.ocr_executed_count == 6
    assert analysis.gating_stats.ocr_skipped_count == 0
    assert ocr.calls == 6
