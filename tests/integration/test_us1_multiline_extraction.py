from __future__ import annotations

from unittest.mock import Mock

import numpy as np

from src.data.models import ContextPattern
from src.services.analysis_service import AnalysisService
from src.services.export_service import ExportService
from src.services.ocr_service import OCRService
from src.services.video_service import VideoService


class _MultilineOCRStub:
    def detect_text_with_diagnostics(self, frame, region):
        del frame, region
        return ["Joined by\nAlice\nRank"], []

    def detect_text(self, frame, region):
        del frame, region
        return ["Joined by\nAlice\nRank"]

    def extract_candidates(
        self,
        lines,
        patterns=None,
        filter_non_matching=False,
        tolerance_threshold=0.75,
    ):
        del filter_non_matching
        service = OCRService()
        return service.extract_candidates(
            lines,
            patterns=patterns,
            filter_non_matching=True,
            tolerance_threshold=tolerance_threshold,
        )


def test_us1_multiline_workflow_extracts_player_name_and_exports_csv(tmp_path) -> None:
    video_service = Mock(spec=VideoService)
    video_service.iterate_frames_with_timestamps.return_value = [
        (0.0, np.zeros((20, 20, 3), dtype=np.uint8))
    ]

    analysis_service = AnalysisService(
        video_service=video_service,
        ocr_service=_MultilineOCRStub(),
    )
    patterns = [
        ContextPattern(id="joined", before_text="Joined by", after_text="Rank", enabled=True)
    ]

    analysis = analysis_service.analyze(
        url="https://youtube.com/watch?v=multiline",
        regions=[(0, 0, 20, 20)],
        start_time=0.0,
        end_time=1.0,
        fps=1,
        context_patterns=patterns,
        filter_non_matching=True,
    )

    export_path = ExportService().export_to_csv(analysis, str(tmp_path), "us1.csv")
    content = export_path.read_text(encoding="utf-8")

    assert any(summary.player_name == "Alice" for summary in analysis.player_summaries)
    assert "PlayerName,StartTimestamp" in content
    assert "Alice" in content


def test_us1_ocr_normalization_contract_raw_lines_to_match() -> None:
    service = OCRService()
    patterns = [
        ContextPattern(id="joined", before_text="Joined by", after_text="Rank", enabled=True)
    ]

    decisions = service.evaluate_lines(
        ["Joined by\nAlice\nRank"],
        patterns=patterns,
        filter_non_matching=True,
        tolerance_threshold=0.75,
    )

    assert len(decisions) == 1
    assert decisions[0]["accepted"] is True
    assert decisions[0]["extracted_name"] == "Alice"
    assert decisions[0]["tested_string_normalized"] == "Joined by Alice Rank"
