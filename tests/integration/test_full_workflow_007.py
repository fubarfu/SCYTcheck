from __future__ import annotations

from pathlib import Path

import numpy as np

from src.data.models import ContextPattern
from src.services.analysis_service import AnalysisService
from src.services.export_service import ExportService


class _WorkflowVideoService:
    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        del url, start_time, end_time, fps, quality
        for idx in range(3):
            frame = np.zeros((20, 20, 3), dtype=np.uint8)
            if idx == 2:
                frame[0:5, 0:5] = 200
            yield float(idx), frame


class _WorkflowOCRService:
    def detect_text(self, frame, region):
        del frame, region
        return ["Played by\nAlice\nRank"]

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


def test_full_workflow_007_analysis_and_export(tmp_path: Path) -> None:
    analysis_service = AnalysisService(
        video_service=_WorkflowVideoService(),
        ocr_service=_WorkflowOCRService(),
    )
    patterns = [
        ContextPattern(id="played", before_text="Played by", after_text="Rank", enabled=True)
    ]

    analysis = analysis_service.analyze(
        url="https://youtube.com/watch?v=workflow007",
        regions=[(0, 0, 10, 10)],
        start_time=0.0,
        end_time=2.0,
        fps=1,
        context_patterns=patterns,
        filter_non_matching=True,
        tolerance_value=0.75,
        gating_enabled=True,
    )

    output = ExportService().export_to_csv(analysis, str(tmp_path), "workflow007.csv")

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "PlayerName,StartTimestamp" in content
    assert "Alice" in content
