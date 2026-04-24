from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np

from src.data.models import (
    AnalysisRuntimeMetrics,
    AppearanceEvent,
    ContextPattern,
    GatingStats,
    LogRecord,
    PlayerSummary,
    TextDetection,
    TimingBreakdown,
    VideoAnalysis,
)
from src.services.logging import should_write_detailed_sidecar
from src.services.ocr_service import OCRService
from src.services.video_service import VideoService

# T020: Precompile whitespace regex for reuse in normalize_name
_RE_WHITESPACE = re.compile(r"\s+")


class AnalysisService:
    def __init__(self, video_service: VideoService, ocr_service: OCRService) -> None:
        self.video_service = video_service
        self.ocr_service = ocr_service

    @staticmethod
    def _estimate_total_frames(start_time: float, end_time: float, fps: int) -> int:
        duration = max(0.0, float(end_time) - float(start_time))
        return max(1, int(duration * max(1, fps)) + 1)

    @staticmethod
    def _crop_region_gray(
        frame: np.ndarray | list[list[int]],
        region: tuple[int, int, int, int],
        frame_gray: np.ndarray | None = None,
    ) -> np.ndarray | None:
        """Crop a region from frame as grayscale.

        Args:
            frame: BGR or grayscale frame array or image-like object
            region: (x, y, width, height) tuple
            frame_gray: Optional pre-computed grayscale of the full frame.
                       If provided, crops from this instead of converting frame.

        Returns:
            Cropped grayscale region as uint8 ndarray, or None if invalid.
        """
        x, y, width, height = region
        if width <= 0 or height <= 0:
            return None

        # Use pre-computed grayscale if provided and valid
        if frame_gray is not None and frame_gray.ndim == 2 and frame_gray.dtype == np.uint8:
            if frame_gray.size == 0:
                return None
            cropped = frame_gray[y : y + height, x : x + width]
            if cropped.size == 0:
                return None
            return cropped

        # Fallback: convert frame (original behavior)
        array = np.asarray(frame)
        if array.size == 0:
            return None
        cropped = array[y : y + height, x : x + width]
        if cropped.size == 0:
            return None
        if cropped.ndim == 3:
            return cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        return cropped

    @staticmethod
    def _compute_frame_region_change(
        prev_crop: np.ndarray,
        curr_crop: np.ndarray,
        gating_threshold: float = 0.02,
    ) -> dict[str, object]:
        if prev_crop.shape != curr_crop.shape:
            return {
                "pixel_diff": 1.0,
                "decision_action": "execute_ocr",
                "reason": "shape_changed",
            }

        pixel_diff = float(cv2.mean(cv2.absdiff(prev_crop, curr_crop))[0] / 255.0)
        pixel_diff = max(0.0, min(pixel_diff, 1.0))
        if pixel_diff < gating_threshold:
            return {
                "pixel_diff": pixel_diff,
                "decision_action": "skip_ocr",
                "reason": "diff_below_threshold",
            }

        return {
            "pixel_diff": pixel_diff,
            "decision_action": "execute_ocr",
            "reason": "diff_above_threshold",
        }

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
        video_quality: str = "best",
        logging_enabled: bool = False,
        tolerance_value: float = 0.75,
        gating_enabled: bool = True,
        gating_threshold: float = 0.02,
        on_log_record: Callable[[LogRecord], None] | None = None,
        output_csv_path: str | Path | None = None,
    ) -> VideoAnalysis:
        tolerance_value = max(0.60, min(float(tolerance_value), 0.95))
        gating_threshold = max(0.0, min(float(gating_threshold), 1.0))
        gating_stats = GatingStats(
            gating_enabled=gating_enabled,
            gating_threshold=gating_threshold,
        )
        analysis = VideoAnalysis(
            url=url,
            context_patterns=context_patterns or [],
            filter_non_matching=filter_non_matching,
            event_gap_threshold_sec=event_gap_threshold_sec,
            video_quality=video_quality,
            logging_enabled=logging_enabled,
            gating_stats=gating_stats,
        )
        frames = self.video_service.iterate_frames_with_timestamps(
            url, start_time, end_time, fps, quality=video_quality
        )
        total_frames = self._estimate_total_frames(start_time, end_time, fps)
        processed_frames = 0
        previous_region_crops: dict[str, np.ndarray] = {}
        previous_region_accepts: dict[str, list[tuple[str, str, str | None]]] = {}
        detailed_logging_enabled = should_write_detailed_sidecar(logging_enabled)
        timing_enabled = detailed_logging_enabled
        decode_ms = 0.0
        gating_ms = 0.0
        ocr_ms = 0.0
        post_processing_ms = 0.0
        total_start = perf_counter() if timing_enabled else 0.0
        frames_output_dir: Path | None = None
        if output_csv_path is not None:
            output_csv = Path(output_csv_path)
            frames_output_dir = output_csv.parent / f"{output_csv.stem}_frames"
            frames_output_dir.mkdir(parents=True, exist_ok=True)

        for idx, (frame_time, frame) in enumerate(frames, start=1):
            processed_frames = idx
            frame_start = perf_counter() if timing_enabled else 0.0

            # T012 & T013: Compute grayscale once per frame when gating enabled (for reuse)
            # Guard: skip when gating disabled or frame is invalid
            frame_gray: np.ndarray | None = None
            if gating_enabled:
                frame_array = np.asarray(frame)
                if frame_array.size > 0:
                    # For BGR frames (3 channels), convert to grayscale once
                    if frame_array.ndim == 3 and frame_array.shape[2] == 3:
                        frame_gray = cv2.cvtColor(frame_array, cv2.COLOR_BGR2GRAY)
                    elif frame_array.ndim == 2:
                        # Already grayscale
                        frame_gray = frame_array
            if timing_enabled:
                decode_ms += (perf_counter() - frame_start) * 1000.0

            for region in regions:
                ocr_diagnostics: list[dict[str, object]] = []
                region_id = f"{region[0]}:{region[1]}:{region[2]}:{region[3]}"
                gating_stats.total_frame_region_pairs += 1

                gating_start = perf_counter() if timing_enabled else 0.0
                current_crop = self._crop_region_gray(frame, region, frame_gray=frame_gray)
                should_skip = False
                decision: dict[str, object] = {
                    "pixel_diff": 1.0,
                    "decision_action": "execute_ocr",
                    "reason": "gating_disabled",
                }
                if (
                    gating_enabled
                    and current_crop is not None
                    and region_id in previous_region_crops
                ):
                    decision = self._compute_frame_region_change(
                        previous_region_crops[region_id],
                        current_crop,
                        gating_threshold=gating_threshold,
                    )
                    should_skip = decision["decision_action"] == "skip_ocr"
                elif gating_enabled:
                    decision = {
                        "pixel_diff": 1.0,
                        "decision_action": "execute_ocr",
                        "reason": "no_previous_frame",
                    }
                if timing_enabled:
                    gating_ms += (perf_counter() - gating_start) * 1000.0

                decision_rows: list[dict[str, object]] | None = None
                accepted_rows: list[tuple[str, str, str | None]] = []
                if should_skip:
                    gating_stats.ocr_skipped_count += 1
                    accepted_rows = list(previous_region_accepts.get(region_id, []))
                else:
                    ocr_start = perf_counter() if timing_enabled else 0.0
                    gating_stats.ocr_executed_count += 1
                    if detailed_logging_enabled and hasattr(
                        self.ocr_service,
                        "detect_text_with_diagnostics",
                    ):
                        tokens, ocr_diagnostics = self.ocr_service.detect_text_with_diagnostics(
                            frame, region
                        )
                    else:
                        tokens = self.ocr_service.detect_text(frame, region)

                    if detailed_logging_enabled and hasattr(self.ocr_service, "evaluate_lines"):
                        try:
                            decision_rows = self.ocr_service.evaluate_lines(
                                tokens,
                                patterns=analysis.context_patterns,
                                filter_non_matching=analysis.filter_non_matching,
                                tolerance_threshold=tolerance_value,
                            )
                        except TypeError:
                            decision_rows = self.ocr_service.evaluate_lines(
                                tokens,
                                patterns=analysis.context_patterns,
                                filter_non_matching=analysis.filter_non_matching,
                            )
                        for decision in decision_rows:
                            if bool(decision["accepted"]):
                                accepted_rows.append(
                                    (
                                        str(decision["raw_string"]),
                                        str(decision["extracted_name"]),
                                        decision["matched_pattern"]
                                        if isinstance(decision["matched_pattern"], str)
                                        else None,
                                    )
                                )
                    else:
                        try:
                            candidates = self.ocr_service.extract_candidates(
                                tokens,
                                patterns=analysis.context_patterns,
                                filter_non_matching=analysis.filter_non_matching,
                                tolerance_threshold=tolerance_value,
                            )
                        except TypeError:
                            candidates = self.ocr_service.extract_candidates(
                                tokens,
                                patterns=analysis.context_patterns,
                                filter_non_matching=analysis.filter_non_matching,
                            )
                        for candidate, pattern_id in candidates:
                            cleaned_candidate = candidate.strip()
                            if cleaned_candidate:
                                accepted_rows.append(
                                    (cleaned_candidate, cleaned_candidate, pattern_id)
                                )

                    if timing_enabled:
                        ocr_ms += (perf_counter() - ocr_start) * 1000.0

                    previous_region_accepts[region_id] = list(accepted_rows)

                if current_crop is not None:
                    previous_region_crops[region_id] = current_crop

                post_start = perf_counter() if timing_enabled else 0.0

                if detailed_logging_enabled:
                    for diagnostic in ocr_diagnostics:
                        if bool(diagnostic.get("accepted")):
                            continue
                        raw = str(diagnostic.get("raw_string", ""))
                        if not raw.strip():
                            continue
                        log_record = LogRecord(
                            timestamp_sec=self.format_timestamp(frame_time),
                            raw_string=raw,
                            tested_string_raw=str(diagnostic.get("tested_string_raw", raw)),
                            tested_string_normalized=str(
                                diagnostic.get(
                                    "tested_string_normalized",
                                    OCRService.normalize_for_matching(raw),
                                )
                            ),
                            accepted=False,
                            rejection_reason=str(
                                diagnostic.get("rejection_reason", "ocr_rejected")
                            ),
                            extracted_name="",
                            region_id=region_id,
                            matched_pattern="",
                            normalized_name="",
                            occurrence_count=0,
                            start_timestamp="",
                            end_timestamp="",
                            representative_region="",
                        )
                        analysis.add_log_record(log_record)
                        if on_log_record is not None:
                            on_log_record(log_record)

                for raw_text, extracted_name, pattern_id in accepted_rows:
                    cleaned = extracted_name.strip()
                    if not cleaned:
                        continue

                    normalized_name = self.normalize_name(cleaned)
                    analysis.add_detection(cleaned, region, frame_time=frame_time)
                    analysis.add_detection_record(
                        TextDetection(
                            raw_ocr_text=raw_text,
                            extracted_name=cleaned,
                            normalized_name=normalized_name,
                            region_id=region_id,
                            frame_time_sec=frame_time,
                            matched_pattern_id=pattern_id,
                        )
                    )

                    if frames_output_dir is not None:
                        x, y, width, height = region
                        frame_array = np.asarray(frame)
                        if frame_array.size > 0 and frame_array.ndim >= 2:
                            max_h, max_w = frame_array.shape[0], frame_array.shape[1]
                            x0, y0 = max(0, x), max(0, y)
                            x1, y1 = min(max_w, x + width), min(max_h, y + height)
                            if x1 > x0 and y1 > y0:
                                crop = frame_array[y0:y1, x0:x1]
                                if crop.size > 0:
                                    candidate_key = re.sub(
                                        r"[^a-zA-Z0-9_-]+",
                                        "_",
                                        f"{normalized_name}_{int(frame_time * 1000)}_{region_id}",
                                    )
                                    cv2.imwrite(
                                        str(frames_output_dir / f"{candidate_key}.png"),
                                        crop,
                                    )

                if detailed_logging_enabled and decision_rows is not None:
                    for decision in decision_rows:
                        if bool(decision["accepted"]):
                            continue
                        raw_string = str(decision.get("raw_string", ""))
                        if not raw_string.strip():
                            continue
                        log_record = LogRecord(
                            timestamp_sec=self.format_timestamp(frame_time),
                            raw_string=raw_string,
                            tested_string_raw=str(decision.get("tested_string_raw", raw_string)),
                            tested_string_normalized=str(
                                decision.get(
                                    "tested_string_normalized",
                                    OCRService.normalize_for_matching(raw_string),
                                )
                            ),
                            accepted=False,
                            rejection_reason=str(decision["rejection_reason"]),
                            extracted_name="",
                            region_id=region_id,
                            matched_pattern="",
                            normalized_name="",
                            occurrence_count=0,
                            start_timestamp="",
                            end_timestamp="",
                            representative_region="",
                        )
                        analysis.add_log_record(log_record)
                        if on_log_record is not None:
                            on_log_record(log_record)

                if timing_enabled:
                    post_processing_ms += (perf_counter() - post_start) * 1000.0

            if on_progress:
                percentage = int((idx / total_frames) * 100)
                on_progress(percentage)

        if processed_frames == 0:
            return analysis

        if on_progress:
            on_progress(100)

        summary_start = perf_counter() if timing_enabled else 0.0
        analysis.set_player_summaries(
            self.build_player_summaries(
                analysis.detections, gap_threshold_sec=analysis.event_gap_threshold_sec
            )
        )
        summary_by_name = {
            summary.normalized_name: summary for summary in analysis.player_summaries
        }
        for detection in analysis.detections:
            summary = summary_by_name.get(detection.normalized_name)
            if summary is None:
                continue
            log_record = LogRecord(
                timestamp_sec=self.format_timestamp(detection.frame_time_sec),
                raw_string=detection.raw_ocr_text,
                tested_string_raw=detection.raw_ocr_text,
                tested_string_normalized=OCRService.normalize_for_matching(detection.raw_ocr_text),
                accepted=True,
                rejection_reason="",
                extracted_name=detection.extracted_name,
                region_id=detection.region_id,
                matched_pattern=detection.matched_pattern_id or "",
                normalized_name=detection.normalized_name,
                occurrence_count=summary.occurrence_count,
                start_timestamp=summary.start_timestamp,
                end_timestamp=self.format_timestamp(summary.last_seen_sec),
                representative_region=summary.representative_region,
            )
            analysis.add_log_record(log_record)
            if on_log_record is not None:
                on_log_record(log_record)

        if timing_enabled:
            post_processing_ms += (perf_counter() - summary_start) * 1000.0
            total_ms = (perf_counter() - total_start) * 1000.0
            analysis.runtime_metrics = AnalysisRuntimeMetrics(
                timing_breakdown=TimingBreakdown(
                    decode_ms=max(0.0, decode_ms),
                    gating_ms=max(0.0, gating_ms),
                    ocr_ms=max(0.0, ocr_ms),
                    post_processing_ms=max(0.0, post_processing_ms),
                    total_ms=max(0.0, total_ms),
                ),
                instrumentation_enabled=True,
                instrumentation_overhead_pct=0.0,
            )

        return analysis

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize names for deduplication: lowercase + trim + collapse spaces."""
        collapsed = _RE_WHITESPACE.sub(" ", (name or "").strip())
        return collapsed.lower()

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        seconds = max(0.0, float(seconds))
        total_ms = int(round(seconds * 1000))
        hours = total_ms // 3_600_000
        remainder = total_ms % 3_600_000
        minutes = remainder // 60_000
        remainder %= 60_000
        secs = remainder // 1000
        millis = remainder % 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

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
                    start_timestamp=cls.format_timestamp(first_seen),
                    normalized_name=normalized_name,
                    occurrence_count=len(events),
                    first_seen_sec=first_seen,
                    last_seen_sec=last_seen,
                    representative_region=representative_region,
                )
            )

        return sorted(summaries, key=lambda summary: summary.normalized_name)
