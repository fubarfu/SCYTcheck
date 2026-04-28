from __future__ import annotations

import base64
import csv
import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
from src.config import AppConfig, AdvancedSettings, load_advanced_settings, load_config
from src.data.models import ContextPattern, LogRecord, TextDetection, VideoAnalysis

from src.web.api.schemas import AnalysisStartRequestDTO, SchemaValidationError
from src.web.app.analysis_adapter import AnalysisAdapter, RunStatus
from src.web.app.history_store import canonicalize_source
from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.services.analysis_service import AnalysisService
from src.services.export_service import ExportService
from src.services.history_service import HistoryService
from src.services.logging import SidecarLogWriter, write_sidecar_log
from src.services.ocr_service import OCRService
from src.services.video_service import VideoService


class _AnalysisCancelled(RuntimeError):
    pass


class _LocalFileVideoService:
    def get_video_info(self, source_path: str, quality: str = "best") -> dict[str, object]:
        del quality
        capture = cv2.VideoCapture(source_path)
        if not capture.isOpened():
            raise ValueError("Could not open local video file.")
        try:
            fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            duration = (frame_count / fps) if fps > 0 else 0.0
            return {
                "title": Path(source_path).stem,
                "duration": duration,
                "width": width,
                "height": height,
            }
        finally:
            capture.release()

    def get_frame_at_time(self, source_path: str, time_seconds: float, quality: str = "best"):
        del quality
        capture = cv2.VideoCapture(source_path)
        if not capture.isOpened():
            raise ValueError("Could not open local video file.")
        try:
            capture.set(cv2.CAP_PROP_POS_MSEC, max(0.0, time_seconds) * 1000.0)
            ok, frame = capture.read()
            if not ok:
                raise ValueError("Could not retrieve frame from local video file.")
            return frame
        finally:
            capture.release()

    def iterate_frames_with_timestamps(
        self,
        source_path: str,
        start_time: float,
        end_time: float,
        fps: int,
        quality: str = "best",
    ):
        del quality
        capture = cv2.VideoCapture(source_path)
        if not capture.isOpened():
            raise ValueError("Could not open local video file.")

        try:
            native_fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
            start_frame = int(max(0.0, start_time) * native_fps)
            end_frame = int(max(start_time, end_time) * native_fps)
            step = max(1, int(native_fps / max(1, fps)))

            capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            current_frame = start_frame
            while current_frame <= end_frame:
                ok, frame = capture.read()
                if not ok:
                    break
                if (current_frame - start_frame) % step == 0:
                    timestamp_sec = current_frame / native_fps
                    yield timestamp_sec, frame
                current_frame += 1
        finally:
            capture.release()


class AnalysisHandler:
    """HTTP-style handler for analysis start/progress/stop/result endpoints."""

    def __init__(
        self,
        adapter: AnalysisAdapter | None = None,
    ) -> None:
        self.adapter = adapter or AnalysisAdapter()
        self.video_service = VideoService()
        self.export_service = ExportService()
        self.history_service = HistoryService()
        self._sidecar_store = ReviewSidecarStore()

    def post_preview(self, payload: dict[str, Any]) -> tuple[int, dict]:
        source_type = str(payload.get("source_type", "")).strip()
        source_value = str(payload.get("source_value", "")).strip()
        time_seconds = float(payload.get("time_seconds", 0.0) or 0.0)
        quality = str(payload.get("video_quality", "best") or "best")

        def build_seek_candidates(requested: float, duration: float | None) -> list[float]:
            safe_max = max(0.0, (duration - 0.001) if duration is not None else requested)
            clamped = max(0.0, min(requested, safe_max))
            candidates = [clamped]
            for backoff in (0.25, 0.5, 1.0, 2.0):
                candidate = max(0.0, clamped - backoff)
                if all(abs(candidate - existing) > 1e-9 for existing in candidates):
                    candidates.append(candidate)
            return candidates

        if source_type not in {"youtube_url", "local_file"}:
            return 400, {
                "error": "validation_error",
                "message": "source_type must be 'youtube_url' or 'local_file'",
            }
        if not source_value:
            return 400, {"error": "validation_error", "message": "source_value is required"}

        try:
            duration_seconds: float | None = None
            if source_type == "youtube_url":
                video_info = self.video_service.get_video_info(source_value, quality=quality)
                raw_duration = float(video_info.get("duration") or 0.0)
                if raw_duration > 0:
                    duration_seconds = raw_duration
                last_error: Exception | None = None
                for candidate_time in build_seek_candidates(time_seconds, duration_seconds):
                    try:
                        frame = self.video_service.get_frame_at_time(
                            source_value,
                            candidate_time,
                            quality=quality,
                        )
                        time_seconds = candidate_time
                        break
                    except Exception as exc:  # pragma: no cover - defensive fallback path
                        last_error = exc
                else:
                    if last_error is None:
                        raise ValueError("Could not retrieve preview frame")
                    raise last_error
            else:
                capture = cv2.VideoCapture(source_value)
                if not capture.isOpened():
                    return 400, {
                        "error": "validation_error",
                        "message": "Could not open local video file",
                    }
                try:
                    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
                    frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
                    raw_duration = (frame_count / fps) if fps > 0 else 0.0
                    if raw_duration > 0:
                        duration_seconds = raw_duration
                    ok = False
                    for candidate_time in build_seek_candidates(time_seconds, duration_seconds):
                        capture.set(cv2.CAP_PROP_POS_MSEC, candidate_time * 1000.0)
                        ok, frame = capture.read()
                        if ok:
                            time_seconds = candidate_time
                            break
                finally:
                    capture.release()
                if not ok:
                    return 400, {
                        "error": "validation_error",
                        "message": "Could not retrieve preview frame",
                    }

            ok, encoded = cv2.imencode(".jpg", frame)
            if not ok:
                return 500, {
                    "error": "encoding_error",
                    "message": "Failed to encode preview frame",
                }
            data_url = (
                "data:image/jpeg;base64,"
                + base64.b64encode(encoded.tobytes()).decode("ascii")
            )
            return 200, {
                "image_url": data_url,
                "width": int(frame.shape[1]),
                "height": int(frame.shape[0]),
                "time_seconds": time_seconds,
                "duration_seconds": duration_seconds,
            }
        except Exception as exc:
            return 400, {"error": "validation_error", "message": str(exc)}

    def post_start(self, payload: dict[str, Any]) -> tuple[int, dict]:
        try:
            dto = AnalysisStartRequestDTO.from_payload(payload)
        except SchemaValidationError as exc:
            return 400, {"error": "validation_error", "message": str(exc)}

        output_folder = Path(dto.output_folder)
        try:
            output_folder.mkdir(parents=True, exist_ok=True)
        except Exception:
            return 400, {"error": "validation_error", "message": "output_folder does not exist"}

        run_id = f"run_{uuid.uuid4().hex[:12]}"
        # Route CSV (and all analysis artifacts) into the per-video workspace folder.
        video_id = ReviewSidecarStore.make_video_id(dto.source_value)
        workspace_root = output_folder / ".scyt_review_workspaces" / video_id
        project_status = "merging" if workspace_root.exists() else "creating"
        output_path = workspace_root / dto.output_filename

        try:
            app_config = load_config()
            persisted = load_advanced_settings()
            advanced = self._merge_advanced_settings(persisted, payload)
            analysis_service = self._create_analysis_service(dto.source_type, advanced)
            context_patterns = self._build_context_patterns(advanced.context_patterns)
            video_info = analysis_service.video_service.get_video_info(
                dto.source_value,
                quality=advanced.video_quality,
            )
            self._validate_regions(dto, video_info)
            duration = float(video_info.get("duration") or 0.0)
            if duration <= 0:
                duration = 60.0
        except Exception as exc:
            return 400, {"error": "validation_error", "message": str(exc)}

        def work() -> str:
            stop_event = self.adapter.get_stop_event(run_id)
            workspace_payload = self._sidecar_store.ensure_workspace_metadata(
                output_path,
                {"source_type": dto.source_type, "source_value": dto.source_value},
            )
            workspace_root.mkdir(parents=True, exist_ok=True)
            metadata_path = workspace_root / "metadata.json"
            existing_metadata: dict[str, Any] = {}
            if metadata_path.exists():
                try:
                    loaded = json.loads(metadata_path.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        existing_metadata = loaded
                except Exception:
                    existing_metadata = {}
            metadata_payload = {
                "project_id": video_id,
                "video_url": dto.source_value,
                "created_date": existing_metadata.get("created_date") or datetime.now(UTC).isoformat(),
                "run_count": int(existing_metadata.get("run_count") or 0) + 1,
                "last_analyzed": datetime.now(UTC).isoformat(),
                "candidate_count_total": int(existing_metadata.get("candidate_count_total") or 0),
                "candidate_count_reviewed": int(existing_metadata.get("candidate_count_reviewed") or 0),
            }
            metadata_path.write_text(json.dumps(metadata_payload, ensure_ascii=True, indent=2), encoding="utf-8")
            frames_output_dir = workspace_root / "frames"
            log_writer_ctx = (
                SidecarLogWriter(str(output_folder), dto.output_filename)
                if advanced.logging_enabled
                else None
            )

            def on_progress(percent: int) -> None:
                status_label = "Creating project" if project_status == "creating" else "Merging with existing project"
                self.adapter.update_progress(run_id, percent, 100, status_label)
                if stop_event is not None and stop_event.is_set():
                    raise _AnalysisCancelled("Analysis cancelled")

            writer = log_writer_ctx.__enter__() if log_writer_ctx is not None else None
            try:
                analysis = analysis_service.analyze(
                    url=dto.source_value,
                    regions=[
                        (region.x, region.y, region.width, region.height)
                        for region in dto.scan_regions
                    ],
                    start_time=0.0,
                    end_time=duration,
                    fps=app_config.sample_fps,
                    on_progress=on_progress,
                    context_patterns=context_patterns,
                    filter_non_matching=advanced.filter_non_matching,
                    event_gap_threshold_sec=advanced.event_gap_threshold_sec,
                    video_quality=advanced.video_quality,
                    logging_enabled=advanced.logging_enabled,
                    tolerance_value=advanced.tolerance_value,
                    gating_enabled=advanced.gating_enabled,
                    gating_threshold=advanced.gating_threshold,
                    on_log_record=writer.write_record if writer is not None else None,
                    output_csv_path=output_path,
                    frames_output_dir=frames_output_dir,
                )
                exported = self.export_service.export_to_csv(
                    analysis,
                    str(workspace_root),
                    dto.output_filename,
                )
                if advanced.logging_enabled:
                    write_sidecar_log(str(output_folder), dto.output_filename, analysis.log_records)
                self._write_review_sidecar(
                    exported,
                    analysis,
                    dto.source_type,
                    dto.source_value,
                    {
                        "scan_regions": [
                            {
                                "x": region.x,
                                "y": region.y,
                                "width": region.width,
                                "height": region.height,
                            }
                            for region in dto.scan_regions
                        ],
                        "output_folder": str(output_folder),
                        "context_patterns": list(advanced.context_patterns),
                        "analysis_settings": AnalysisService.history_settings_snapshot(
                            ocr_confidence_threshold=advanced.ocr_confidence_threshold,
                            tolerance_value=advanced.tolerance_value,
                            event_gap_threshold_sec=advanced.event_gap_threshold_sec,
                            gating_enabled=advanced.gating_enabled,
                            gating_threshold=advanced.gating_threshold,
                            video_quality=advanced.video_quality,
                            filter_non_matching=advanced.filter_non_matching,
                            logging_enabled=advanced.logging_enabled,
                        ),
                    },
                )
                merge_result = self.history_service.merge_run(
                    source_type=dto.source_type,
                    source_value=dto.source_value,
                    canonical_source=canonicalize_source(dto.source_type, dto.source_value),
                    duration_seconds=int(duration) if duration > 0 else None,
                    result_csv_path=str(exported),
                    output_folder=str(output_folder),
                    context={
                        "scan_region": {
                            "x": dto.scan_regions[0].x,
                            "y": dto.scan_regions[0].y,
                            "width": dto.scan_regions[0].width,
                            "height": dto.scan_regions[0].height,
                        },
                        "context_patterns": list(advanced.context_patterns),
                        "analysis_settings": AnalysisService.history_settings_snapshot(
                            ocr_confidence_threshold=advanced.ocr_confidence_threshold,
                            tolerance_value=advanced.tolerance_value,
                            event_gap_threshold_sec=advanced.event_gap_threshold_sec,
                            gating_enabled=advanced.gating_enabled,
                            gating_threshold=advanced.gating_threshold,
                            video_quality=advanced.video_quality,
                            filter_non_matching=advanced.filter_non_matching,
                            logging_enabled=advanced.logging_enabled,
                        ),
                    },
                )
                self.adapter.set_history_metadata(
                    run_id=run_id,
                    history_id=str(merge_result["history_id"]),
                    history_run_id=str(merge_result["run_id"]),
                )
                self.adapter.update_progress(run_id, 100, 100, "Completed")
                return str(exported)
            finally:
                if log_writer_ctx is not None:
                    log_writer_ctx.__exit__(None, None, None)

        try:
            self.adapter.start(run_id, work)
            self.adapter.set_project_metadata(run_id, project_status, video_id)
        except ValueError as exc:
            return 409, {"error": "conflict", "message": str(exc)}

        message = (
            f"Creating new project for {dto.source_value}"
            if project_status == "creating"
            else "Merging results with existing project"
        )
        return 202, {
            "run_id": run_id,
            "analysis_id": run_id,
            "video_id": video_id,
            "project_status": project_status,
            "status": RunStatus.RUNNING.value,
            "message": message,
        }

    @staticmethod
    def _validate_regions(
        dto: AnalysisStartRequestDTO,
        video_info: dict[str, object],
    ) -> None:
        frame_width = int(video_info.get("width") or 0)
        frame_height = int(video_info.get("height") or 0)
        if frame_width <= 0 or frame_height <= 0:
            return

        for index, region in enumerate(dto.scan_regions, start=1):
            if region.x >= frame_width or region.y >= frame_height:
                raise SchemaValidationError(
                    f"scan region {index} origin is outside frame bounds {frame_width}x{frame_height}"
                )
            if region.x + region.width > frame_width or region.y + region.height > frame_height:
                raise SchemaValidationError(
                    f"scan region {index} exceeds frame bounds {frame_width}x{frame_height}"
                )

    @staticmethod
    def _build_context_patterns(items: list[dict[str, object]]) -> list[ContextPattern]:
        patterns: list[ContextPattern] = []
        for index, item in enumerate(items):
            patterns.append(
                ContextPattern(
                    id=str(item.get("id", f"pattern-{index}")),
                    before_text=(
                        str(item["before_text"]) if item.get("before_text") is not None else None
                    ),
                    after_text=(
                        str(item["after_text"]) if item.get("after_text") is not None else None
                    ),
                    enabled=bool(item.get("enabled", True)),
                )
            )
        return patterns

    @staticmethod
    def _merge_advanced_settings(
        base: AdvancedSettings,
        payload: dict[str, Any],
    ) -> AdvancedSettings:
        return AdvancedSettings(
            context_patterns=list(payload.get("context_patterns", base.context_patterns)),
            filter_non_matching=bool(payload.get("filter_non_matching", base.filter_non_matching)),
            event_gap_threshold_sec=float(
                payload.get("event_gap_threshold_sec", base.event_gap_threshold_sec)
            ),
            ocr_confidence_threshold=int(
                payload.get("ocr_confidence_threshold", base.ocr_confidence_threshold)
            ),
            paddleocr_model_root=(
                str(payload.get("paddleocr_model_root"))
                if payload.get("paddleocr_model_root") not in (None, "")
                else base.paddleocr_model_root
            ),
            video_quality=str(payload.get("video_quality", base.video_quality) or "best"),
            logging_enabled=bool(payload.get("logging_enabled", base.logging_enabled)),
            tolerance_value=float(payload.get("tolerance_value", base.tolerance_value)),
            gating_enabled=bool(payload.get("gating_enabled", base.gating_enabled)),
            gating_threshold=float(payload.get("gating_threshold", base.gating_threshold)),
        )

    @staticmethod
    def _candidate_id(detection: TextDetection) -> str:
        return re.sub(
            r"[^a-zA-Z0-9_-]+",
            "_",
            f"{detection.normalized_name}_{int(detection.frame_time_sec * 1000)}_{detection.region_id}",
        )

    def _write_review_sidecar(
        self,
        csv_path: Path,
        analysis: VideoAnalysis,
        source_type: str,
        source_value: str,
        context: dict[str, Any],
    ) -> None:
        candidates: list[dict[str, Any]] = []
        for detection in analysis.detections:
            candidates.append(
                {
                    "candidate_id": self._candidate_id(detection),
                    "extracted_name": detection.extracted_name,
                    "start_timestamp": AnalysisService.format_timestamp(detection.frame_time_sec),
                    "status": "pending",
                    "region_id": detection.region_id,
                    "normalized_name": detection.normalized_name,
                }
            )

        payload = {
            "source_type": source_type,
            "source_value": source_value,
            "scan_regions": list(context.get("scan_regions", [])),
            "scan_region": dict((context.get("scan_regions") or [{}])[0]),
            "output_folder": str(context.get("output_folder", "")),
            "context_patterns": list(context.get("context_patterns", [])),
            "analysis_settings": dict(context.get("analysis_settings", {})),
            "candidates": candidates,
            "candidates_original": [dict(candidate) for candidate in candidates],
            "action_history": [],
        }
        self._sidecar_store.save(csv_path, payload)

    def _create_analysis_service(
        self,
        source_type: str,
        advanced: AdvancedSettings,
    ) -> AnalysisService:
        if source_type == "youtube_url":
            video_service: Any = self.video_service
        else:
            video_service = _LocalFileVideoService()

        ocr_service = OCRService(
            confidence_threshold=advanced.ocr_confidence_threshold,
            paddleocr_model_root=advanced.paddleocr_model_root,
        )
        return AnalysisService(video_service=video_service, ocr_service=ocr_service)

    def get_progress(self, run_id: str) -> tuple[int, dict]:
        state = self.adapter.progress(run_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"run_id {run_id} not found"}

        total = max(1, int(state.frames_estimated_total or 0))
        progress_percent = int(min(100, max(0, round((state.frames_processed / total) * 100))))

        return 200, {
            "run_id": state.run_id,
            "analysis_id": state.run_id,
            "status": state.status.value,
            "project_status": state.project_status or "creating",
            "message": state.stage_label,
            "stage_label": state.stage_label,
            "frames_processed": state.frames_processed,
            "frames_estimated_total": state.frames_estimated_total,
            "progress_percent": progress_percent,
            "review_ready": state.status == RunStatus.COMPLETED,
            "video_id": state.video_id,
        }

    def post_stop(self, run_id: str) -> tuple[int, dict]:
        state = self.adapter.stop(run_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"run_id {run_id} not found"}
        return 202, {"run_id": state.run_id, "status": state.status.value}

    def get_result(self, run_id: str) -> tuple[int, dict]:
        state = self.adapter.progress(run_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"run_id {run_id} not found"}
        if state.status not in {RunStatus.COMPLETED, RunStatus.FAILED}:
            return 202, {"run_id": run_id, "status": state.status.value}

        partial = state.status == RunStatus.FAILED
        return 200, {
            "run_id": run_id,
            "status": state.status.value,
            "csv_path": state.output_csv_path,
            "history_id": state.history_id,
            "history_run_id": state.history_run_id,
            "partial": partial,
        }
