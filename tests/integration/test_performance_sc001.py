from __future__ import annotations

import time
from unittest.mock import Mock

import numpy as np

from src.data.models import ContextPattern
from src.services.analysis_service import AnalysisService
from src.services.ocr_service import OCRService
from src.services.video_service import VideoService
from tests.integration.helpers.perf_helpers import benchmark_callable


def test_sc001_analysis_of_ten_minute_video_completes_within_target() -> None:
    video_service = Mock(spec=VideoService)
    frames = [np.zeros((720, 1280, 3), dtype=np.uint8) for _ in range(10)]

    def iterate_frames_with_timestamps(
        url: str, start_time: float, end_time: float, fps: int, quality: str = "best"
    ):
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


def test_sc001_one_hour_iteration_target_with_sequential_path() -> None:
    video_service = Mock(spec=VideoService)
    ocr_service = Mock(spec=OCRService)
    ocr_service.detect_text.return_value = ["Player: Alice"]
    ocr_service.extract_candidates.return_value = [("Alice", "pattern-1")]

    frame_count = 3600
    frames = [np.zeros((8, 8, 3), dtype=np.uint8) for _ in range(frame_count)]

    def iterate_frames_with_timestamps(
        url: str, start_time: float, end_time: float, fps: int, quality: str = "best"
    ):
        del url, start_time, end_time, fps, quality
        for i, frame in enumerate(frames):
            yield float(i), frame

    video_service.iterate_frames_with_timestamps.side_effect = iterate_frames_with_timestamps
    analysis_service = AnalysisService(video_service=video_service, ocr_service=ocr_service)

    elapsed = benchmark_callable(
        lambda: analysis_service.analyze(
            url="https://youtube.com/watch?v=onehour",
            regions=[(1, 1, 2, 2)],
            start_time=0.0,
            end_time=3600.0,
            fps=1,
        ),
        repeat=1,
    )

    assert elapsed < 180.0
    kwargs = video_service.iterate_frames_with_timestamps.call_args.kwargs
    assert kwargs["quality"] == "best"


def test_sc001_two_hour_iteration_scaling_target() -> None:
    video_service = Mock(spec=VideoService)
    ocr_service = Mock(spec=OCRService)
    ocr_service.detect_text.return_value = ["Player: Alice"]
    ocr_service.extract_candidates.return_value = [("Alice", "pattern-1")]

    def iterate_frames_with_timestamps(
        url: str, start_time: float, end_time: float, fps: int, quality: str = "best"
    ):
        del url, start_time, end_time, fps, quality
        for i in range(7200):
            yield float(i), np.zeros((4, 4, 3), dtype=np.uint8)

    video_service.iterate_frames_with_timestamps.side_effect = iterate_frames_with_timestamps
    analysis_service = AnalysisService(video_service=video_service, ocr_service=ocr_service)

    started = time.perf_counter()
    result = analysis_service.analyze(
        url="https://youtube.com/watch?v=twohour",
        regions=[(0, 0, 2, 2)],
        start_time=0.0,
        end_time=7200.0,
        fps=1,
    )
    elapsed = time.perf_counter() - started

    assert result.player_summaries
    assert elapsed < 300.0


def test_sc001_multiline_recall_meets_95_percent_target() -> None:
    service = OCRService()
    pattern = ContextPattern(id="joined", before_text="Joined by", after_text="Rank", enabled=True)

    lines = [
        "Joined by\nAlice\nRank",
        "Joined by\nBob\nRank",
        "Joined by\nCarol\nRank",
        "Joined by\nDora\nRank",
        "Joined by\nEvan\nRank",
        "Joined by\nFinn\nRank",
        "Joined by\nGina\nRank",
        "Joined by\nHugo\nRank",
        "Joined by\nIvy\nRank",
        "Joined by\nJay\nRank",
    ]

    accepted = 0
    for line in lines:
        decisions = service.evaluate_lines(
            [line],
            patterns=[pattern],
            filter_non_matching=True,
            tolerance_threshold=0.75,
        )
        accepted += sum(1 for decision in decisions if bool(decision["accepted"]))
    recall = accepted / len(lines)

    assert recall >= 0.95
