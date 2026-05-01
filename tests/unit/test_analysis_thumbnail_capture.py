from __future__ import annotations

from pathlib import Path

import numpy as np

from src.services.analysis_service import AnalysisService


class _VideoServiceSingleFrameStub:
    def __init__(self, frame: np.ndarray) -> None:
        self._frame = frame

    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        del url, start_time, end_time, fps, quality
        yield 1.25, self._frame


class _OCRServiceAcceptedStub:
    def detect_text(self, frame, region):
        del frame, region
        return ["Player Alpha"]

    def extract_candidates(
        self,
        tokens,
        patterns=None,
        filter_non_matching=False,
        tolerance_threshold=0.75,
    ):
        del patterns, filter_non_matching, tolerance_threshold
        return [(str(tokens[0]), None)]


def test_analysis_writes_frame_thumbnail_alongside_result_csv(tmp_path: Path) -> None:
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    frame[2:8, 3:11] = 255

    service = AnalysisService(
        video_service=_VideoServiceSingleFrameStub(frame),
        ocr_service=_OCRServiceAcceptedStub(),
    )

    csv_path = tmp_path / "result.csv"
    service.analyze(
        url="https://youtube.com/watch?v=abc123xyz00",
        regions=[(3, 2, 8, 6)],
        start_time=0.0,
        end_time=2.0,
        fps=1,
        output_csv_path=csv_path,
    )

    frames_dir = tmp_path / "result_frames"
    assert frames_dir.exists()
    pngs = list(frames_dir.glob("*.png"))
    assert len(pngs) >= 1
