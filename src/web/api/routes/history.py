from __future__ import annotations

from typing import Any

from src.services.history_service import HistoryService
from src.web.api.schemas import (
    HistoryMergeRunRequestDTO,
    HistoryReopenRequestDTO,
    SchemaValidationError,
)


class HistoryHandler:
    """HTTP-style handler for history list/get/merge/reopen/delete endpoints."""

    def __init__(self, service: HistoryService | None = None) -> None:
        self.service = service or HistoryService()

    def get_videos(self, query: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        query = query or {}
        include_deleted = str(query.get("include_deleted", "false")).lower() in {
            "1",
            "true",
            "yes",
        }
        try:
            limit = int(query.get("limit", 200))
        except (TypeError, ValueError):
            return 400, {"error": "validation_error", "message": "limit must be an integer"}

        body = self.service.list_videos(include_deleted=include_deleted, limit=limit)
        return 200, body

    def get_video(self, history_id: str) -> tuple[int, dict[str, Any]]:
        try:
            return 200, self.service.get_video(history_id)
        except FileNotFoundError as exc:
            return 404, {"error": "not_found", "message": str(exc)}

    def post_merge_run(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        try:
            dto = HistoryMergeRunRequestDTO.from_payload(payload)
        except SchemaValidationError as exc:
            return 400, {"error": "validation_error", "message": str(exc)}

        try:
            body = self.service.merge_run(
                source_type=dto.source_type,
                source_value=dto.source_value,
                canonical_source=dto.canonical_source,
                duration_seconds=dto.duration_seconds,
                result_csv_path=str(dto.result_csv_path),
                output_folder=str(dto.output_folder),
                context={
                    "scan_region": dto.context.scan_region,
                    "context_patterns": dto.context.context_patterns,
                    "analysis_settings": dto.context.analysis_settings,
                },
            )
            return 200, body
        except ValueError as exc:
            return 400, {"error": "validation_error", "message": str(exc)}
        except Exception:
            return 500, {"error": "internal_error", "message": "Unexpected server error"}

    def post_reopen(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        try:
            dto = HistoryReopenRequestDTO.from_payload(payload)
        except SchemaValidationError as exc:
            return 400, {"error": "validation_error", "message": str(exc)}

        try:
            return 200, self.service.reopen(dto.history_id)
        except FileNotFoundError as exc:
            return 404, {"error": "not_found", "message": str(exc)}
        except Exception:
            return 500, {"error": "internal_error", "message": "Unexpected server error"}

    def delete_video(self, history_id: str) -> tuple[int, dict[str, Any]]:
        try:
            return 200, self.service.delete_video(history_id)
        except FileNotFoundError as exc:
            return 404, {"error": "not_found", "message": str(exc)}
