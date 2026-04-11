from __future__ import annotations

import time
from unittest.mock import Mock

import numpy as np

from src.services.analysis_service import AnalysisService
from src.services.ocr_service import OCRService
from src.services.video_service import VideoService


def test_sc001_analysis_of_ten_minute_video_completes_within_target() -> None:
    video_service = Mock(spec=VideoService)
    frames = [np.zeros((720, 1280, 3), dtype=np.uint8) for _ in range(10)]

    def iterate_frames_with_timestamps(url: str, start_time: float, end_time: float, fps: int, quality: str = "best"):
        del url, end_time, fps
        for index, frame in enumerate(frames):
            yield start_time + (index * 60.0), frame

    video_service.iterate_frames_with_timestamps.side_effect = iterate_frames_with_timestamps
    ocr_service = Mock(spec=OCRService)
    ocr_service.detect_text.return_value = ["Player: Alice"]
    ocr_service.extract_candidates.return_value = [("Alice", "pattern-1")]

    analysis_service = AnalysisService(video_service=video_service, ocr_service=ocr_service)

    started_at = time.perf_counter()
    analysis = analysis_service.analyze(
        url="https://youtube.com/watch?v=tenminutevideo",
        regions=[(100, 100, 200, 150)],
        start_time=0.0,
        end_time=600.0,
        fps=1,
    )
    elapsed = time.perf_counter() - started_at

    assert elapsed < 300.0
    assert analysis.player_summaries
