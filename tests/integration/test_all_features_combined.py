from __future__ import annotations

import numpy as np

from src.data.models import ContextPattern
from src.services.analysis_service import AnalysisService


class _CombinedVideoService:
    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        del url, start_time, end_time, fps, quality
        frame0 = np.zeros((20, 20, 3), dtype=np.uint8)
        frame1 = frame0.copy()
        frame2 = frame0.copy()
        frame2[0:5, 0:5] = 100
        return [(0.0, frame0), (1.0, frame1), (2.0, frame2)]


class _CombinedOCRService:
    def detect_text(self, frame, region):
        del frame, region
        return ["Pxyzed by\nAlice\nRank"]

    def extract_candidates(
        self,
        lines,
        patterns=None,
        filter_non_matching=False,
        tolerance_threshold=0.75,
    ):
        from src.services.ocr_service import OCRService

        service = OCRService()
        return service.extract_candidates(
            lines,
            patterns=patterns,
            filter_non_matching=filter_non_matching,
            tolerance_threshold=tolerance_threshold,
        )


def test_all_features_combined_multiline_tolerance_and_gating() -> None:
    service = AnalysisService(
        video_service=_CombinedVideoService(),
        ocr_service=_CombinedOCRService(),
    )
    patterns = [
        ContextPattern(id="played", before_text="Played by", after_text="Rank", enabled=True)
    ]

    analysis = service.analyze(
        url="https://youtube.com/watch?v=combined",
        regions=[(0, 0, 10, 10)],
        start_time=0.0,
        end_time=2.0,
        fps=1,
        context_patterns=patterns,
        filter_non_matching=True,
        tolerance_value=0.65,
        gating_enabled=True,
        gating_threshold=0.02,
    )

    assert any(summary.player_name == "Alice" for summary in analysis.player_summaries)
    assert analysis.gating_stats is not None
    assert analysis.gating_stats.ocr_skipped_count >= 1
