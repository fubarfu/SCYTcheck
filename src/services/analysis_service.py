from __future__ import annotations

from collections.abc import Callable
import re

from src.data.models import AppearanceEvent, ContextPattern, PlayerSummary, TextDetection, VideoAnalysis
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
        context_patterns: list[ContextPattern] | None = None,
        filter_non_matching: bool = False,
        event_gap_threshold_sec: float = 1.0,
    ) -> VideoAnalysis:
        analysis = VideoAnalysis(
            url=url,
            context_patterns=context_patterns or [],
            filter_non_matching=filter_non_matching,
            event_gap_threshold_sec=event_gap_threshold_sec,
        )
        frames = list(self.video_service.iterate_frames_with_timestamps(url, start_time, end_time, fps))
        total_frames = len(frames)

        if total_frames == 0:
            return analysis

        for idx, (frame_time, frame) in enumerate(frames, start=1):
            for region in regions:
                tokens = self.ocr_service.detect_text(frame, region)
                candidates = self.ocr_service.extract_candidates(
                    tokens,
                    patterns=analysis.context_patterns,
                    filter_non_matching=analysis.filter_non_matching,
                )
                for candidate, pattern_id in candidates:
                    cleaned = candidate.strip()
                    if not cleaned:
                        continue

                    normalized_name = self.normalize_name(cleaned)
                    region_id = f"{region[0]}:{region[1]}:{region[2]}:{region[3]}"
                    analysis.add_detection(cleaned, region, frame_time=frame_time)
                    analysis.add_detection_record(
                        TextDetection(
                            raw_ocr_text=cleaned,
                            extracted_name=cleaned,
                            normalized_name=normalized_name,
                            region_id=region_id,
                            frame_time_sec=frame_time,
                            matched_pattern_id=pattern_id,
                        )
                    )

            if on_progress:
                percentage = int((idx / total_frames) * 100)
                on_progress(percentage)

        analysis.set_player_summaries(
            self.build_player_summaries(analysis.detections, gap_threshold_sec=analysis.event_gap_threshold_sec)
        )

        return analysis

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize names for deduplication: lowercase + trim + collapse spaces."""
        collapsed = re.sub(r"\s+", " ", (name or "").strip())
        return collapsed.lower()

    @staticmethod
    def merge_appearance_events(
        detections: list[tuple[str, float, str]],
        gap_threshold_sec: float = 1.0,
    ) -> list[AppearanceEvent]:
        """Merge detections into appearance events by normalized name and gap threshold.

        Each detection tuple is (normalized_name, frame_time_sec, region_id).
        """
        if not detections:
            return []

        sorted_detections = sorted(detections, key=lambda item: (item[0], item[1]))
        events: list[AppearanceEvent] = []
        current: AppearanceEvent | None = None

        for normalized_name, frame_time_sec, region_id in sorted_detections:
            if current is None or current.normalized_name != normalized_name:
                if current is not None:
                    events.append(current)
                current = AppearanceEvent(
                    normalized_name=normalized_name,
                    display_name=normalized_name,
                    start_time_sec=frame_time_sec,
                    end_time_sec=frame_time_sec,
                    region_ids={region_id},
                )
                continue

            if frame_time_sec - current.end_time_sec <= gap_threshold_sec:
                current.end_time_sec = frame_time_sec
                current.region_ids.add(region_id)
            else:
                events.append(current)
                current = AppearanceEvent(
                    normalized_name=normalized_name,
                    display_name=normalized_name,
                    start_time_sec=frame_time_sec,
                    end_time_sec=frame_time_sec,
                    region_ids={region_id},
                )

        if current is not None:
            events.append(current)

        return events

    @classmethod
    def build_player_summaries(
        cls,
        detections: list[TextDetection],
        gap_threshold_sec: float = 1.0,
    ) -> list[PlayerSummary]:
        if not detections:
            return []

        merged_events = cls.merge_appearance_events(
            [
                (detection.normalized_name, detection.frame_time_sec, detection.region_id)
                for detection in detections
            ],
            gap_threshold_sec=gap_threshold_sec,
        )

        grouped: dict[str, list[AppearanceEvent]] = {}
        for event in merged_events:
            grouped.setdefault(event.normalized_name, []).append(event)

        representative_names: dict[str, str] = {}
        for detection in detections:
            if detection.normalized_name not in representative_names:
                representative_names[detection.normalized_name] = detection.extracted_name.strip()

        summaries: list[PlayerSummary] = []
        for normalized_name, events in grouped.items():
            first_seen = min(event.start_time_sec for event in events)
            last_seen = max(event.end_time_sec for event in events)
            representative_region = sorted(events[0].region_ids)[0] if events[0].region_ids else ""
            summaries.append(
                PlayerSummary(
                    player_name=representative_names.get(normalized_name, normalized_name),
                    normalized_name=normalized_name,
                    occurrence_count=len(events),
                    first_seen_sec=first_seen,
                    last_seen_sec=last_seen,
                    representative_region=representative_region,
                )
            )

        return sorted(summaries, key=lambda summary: summary.normalized_name)
