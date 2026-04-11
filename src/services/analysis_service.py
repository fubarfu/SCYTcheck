from __future__ import annotations

from collections.abc import Callable

from src.data.models import VideoAnalysis
from src.services.ocr_service import OCRService
from src.services.video_service import VideoService


class AnalysisService:
    def __init__(self, video_service: VideoService, ocr_service: OCRService) -> None:
        self.video_service = video_service
        self.ocr_service = ocr_service

    def analyze(
        self,
        url: str,
        regions: list[tuple[int, int, int, int]],
        start_time: float,
        end_time: float,
        fps: int,
        on_progress: Callable[[int], None] | None = None,
    ) -> VideoAnalysis:
        analysis = VideoAnalysis(url=url)
        frames = list(self.video_service.get_frames_in_range(url, start_time, end_time, fps))
        total_frames = len(frames)

        if total_frames == 0:
            return analysis

        for idx, frame in enumerate(frames, start=1):
            for region in regions:
                for token in self.ocr_service.detect_text(frame, region):
                    analysis.add_detection(token, region)

            if on_progress:
                percentage = int((idx / total_frames) * 100)
                on_progress(percentage)

        return analysis
