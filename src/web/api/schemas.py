from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config import default_project_location

class SchemaValidationError(ValueError):
    """Raised when incoming API payload data is invalid."""


@dataclass(frozen=True)
class ScanRegionDTO:
    x: int
    y: int
    width: int
    height: int

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> ScanRegionDTO:
        required = ("x", "y", "width", "height")
        missing = [key for key in required if key not in payload]
        if missing:
            raise SchemaValidationError(f"Missing scan region fields: {', '.join(missing)}")

        x = int(payload["x"])
        y = int(payload["y"])
        width = int(payload["width"])
        height = int(payload["height"])
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise SchemaValidationError("Scan region must be positive and in-bounds")
        return ScanRegionDTO(x=x, y=y, width=width, height=height)


@dataclass(frozen=True)
class AnalysisStartRequestDTO:
    source_type: str
    source_value: str
    output_folder: str
    output_filename: str
    scan_regions: list[ScanRegionDTO]

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> AnalysisStartRequestDTO:
        source_type = str(payload.get("source_type", "")).strip()
        source_value = str(payload.get("source_value", "")).strip()
        output_folder = str(payload.get("output_folder", payload.get("project_location", ""))).strip()
        output_filename = str(payload.get("output_filename", "")).strip()
        if source_type not in {"youtube_url", "local_file"}:
            raise SchemaValidationError("source_type must be 'youtube_url' or 'local_file'")
        if not source_value:
            raise SchemaValidationError("source_value is required")
        if not output_folder:
            output_folder = str(default_project_location())
        if not output_filename:
            output_filename = "result_latest.csv"
        scan_regions_payload = payload.get("scan_regions")
        scan_regions: list[ScanRegionDTO] = []

        if isinstance(scan_regions_payload, list) and scan_regions_payload:
            for item in scan_regions_payload:
                if not isinstance(item, dict):
                    raise SchemaValidationError("scan_regions must contain objects")
                scan_regions.append(ScanRegionDTO.from_payload(item))
        else:
            scan_region_payload = payload.get("scan_region")
            if not isinstance(scan_region_payload, dict):
                raise SchemaValidationError("scan_region must be an object")
            scan_regions = [ScanRegionDTO.from_payload(scan_region_payload)]

        return AnalysisStartRequestDTO(
            source_type=source_type,
            source_value=source_value,
            output_folder=output_folder,
            output_filename=output_filename,
            scan_regions=scan_regions,
        )


@dataclass(frozen=True)
class ReviewLoadRequestDTO:
    csv_path: Path

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> ReviewLoadRequestDTO:
        csv_path_raw = str(payload.get("csv_path", "")).strip()
        if not csv_path_raw:
            raise SchemaValidationError("csv_path is required")
        csv_path = Path(csv_path_raw)
        if csv_path.suffix.lower() != ".csv":
            raise SchemaValidationError("csv_path must point to a .csv file")
        return ReviewLoadRequestDTO(csv_path=csv_path)


@dataclass(frozen=True)
class HistoryContextDTO:
    scan_region: dict[str, int]
    context_patterns: list[dict[str, Any]]
    analysis_settings: dict[str, Any]

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> HistoryContextDTO:
        scan_region = payload.get("scan_region")
        if not isinstance(scan_region, dict):
            raise SchemaValidationError("context.scan_region must be an object")
        region = ScanRegionDTO.from_payload(scan_region)

        context_patterns_raw = payload.get("context_patterns", [])
        if not isinstance(context_patterns_raw, list):
            raise SchemaValidationError("context.context_patterns must be an array")

        settings_raw = payload.get("analysis_settings", {})
        if not isinstance(settings_raw, dict):
            raise SchemaValidationError("context.analysis_settings must be an object")

        return HistoryContextDTO(
            scan_region={
                "x": region.x,
                "y": region.y,
                "width": region.width,
                "height": region.height,
            },
            context_patterns=[dict(item) for item in context_patterns_raw if isinstance(item, dict)],
            analysis_settings=dict(settings_raw),
        )


@dataclass(frozen=True)
class HistoryMergeRunRequestDTO:
    source_type: str
    source_value: str
    canonical_source: str
    duration_seconds: int | None
    result_csv_path: Path
    output_folder: Path
    context: HistoryContextDTO

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> HistoryMergeRunRequestDTO:
        source_type = str(payload.get("source_type", "")).strip()
        source_value = str(payload.get("source_value", "")).strip()
        canonical_source = str(payload.get("canonical_source", "")).strip()
        result_csv_path_raw = str(payload.get("result_csv_path", "")).strip()
        output_folder_raw = str(payload.get("output_folder", "")).strip()

        if source_type not in {"youtube_url", "local_file"}:
            raise SchemaValidationError("source_type must be 'youtube_url' or 'local_file'")
        if not source_value:
            raise SchemaValidationError("source_value is required")
        if not canonical_source:
            raise SchemaValidationError("canonical_source is required")
        if not result_csv_path_raw:
            raise SchemaValidationError("result_csv_path is required")
        if not output_folder_raw:
            raise SchemaValidationError("output_folder is required")

        duration_raw = payload.get("duration_seconds")
        duration_seconds: int | None = None
        if duration_raw is not None:
            try:
                duration_seconds = int(duration_raw)
            except (TypeError, ValueError):
                duration_seconds = None
            if duration_seconds is not None and duration_seconds < 0:
                duration_seconds = None

        context_payload = payload.get("context")
        if not isinstance(context_payload, dict):
            raise SchemaValidationError("context is required")

        result_csv_path = Path(result_csv_path_raw)
        output_folder = Path(output_folder_raw)

        return HistoryMergeRunRequestDTO(
            source_type=source_type,
            source_value=source_value,
            canonical_source=canonical_source,
            duration_seconds=duration_seconds,
            result_csv_path=result_csv_path,
            output_folder=output_folder,
            context=HistoryContextDTO.from_payload(context_payload),
        )


@dataclass(frozen=True)
class HistoryReopenRequestDTO:
    history_id: str

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> HistoryReopenRequestDTO:
        history_id = str(payload.get("history_id", "")).strip()
        if not history_id:
            raise SchemaValidationError("history_id is required")
        return HistoryReopenRequestDTO(history_id=history_id)


REVIEW_ACTION_TYPES = frozenset(
    {
        "confirm",
        "reject",
        "unreject",
        "deselect",
        "toggle_collapse",
        "edit",
        "remove",
        "move_candidate",
        "merge_groups",
        "reorder_group",
    }
)


@dataclass(frozen=True)
class ReviewActionRequestDTO:
    action_type: str
    target_ids: list[str]
    payload: dict[str, Any]

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> ReviewActionRequestDTO:
        action_type = str(payload.get("action_type", "")).strip()
        if action_type not in REVIEW_ACTION_TYPES:
            raise SchemaValidationError(
                f"action_type must be one of: {', '.join(sorted(REVIEW_ACTION_TYPES))}"
            )

        target_ids_raw = payload.get("target_ids", [])
        if not isinstance(target_ids_raw, list):
            raise SchemaValidationError("target_ids must be a list")
        target_ids = [str(item).strip() for item in target_ids_raw if str(item).strip()]

        if action_type in {"confirm", "reject", "unreject", "edit", "remove"} and not target_ids:
            raise SchemaValidationError("target_ids must be a non-empty list")

        action_payload = payload.get("payload", {})
        if not isinstance(action_payload, dict):
            raise SchemaValidationError("payload must be an object")

        return ReviewActionRequestDTO(
            action_type=action_type,
            target_ids=target_ids,
            payload=action_payload,
        )


@dataclass(frozen=True)
class ReviewToggleCollapseRequestDTO:
    group_id: str
    is_collapsed: bool | None = None

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> ReviewToggleCollapseRequestDTO:
        group_id = str(payload.get("group_id", "")).strip()
        if not group_id:
            raise SchemaValidationError("payload.group_id is required")

        collapsed_raw = payload.get("is_collapsed")
        collapsed: bool | None
        if collapsed_raw is None:
            collapsed = None
        else:
            collapsed = bool(collapsed_raw)

        return ReviewToggleCollapseRequestDTO(group_id=group_id, is_collapsed=collapsed)


@dataclass(frozen=True)
class ReviewConfirmCandidateRequestDTO:
    group_id: str
    candidate_id: str

    @staticmethod
    def from_action(action: ReviewActionRequestDTO) -> ReviewConfirmCandidateRequestDTO:
        group_id = str(action.payload.get("group_id", "")).strip()
        candidate_id = action.target_ids[0] if action.target_ids else ""
        if not group_id:
            raise SchemaValidationError("payload.group_id is required")
        if not candidate_id:
            raise SchemaValidationError("target_ids must include a candidate id")
        return ReviewConfirmCandidateRequestDTO(group_id=group_id, candidate_id=candidate_id)


@dataclass(frozen=True)
class ReviewValidationFeedbackDTO:
    is_valid: bool
    candidate_name: str
    message: str | None = None
    conflict_group_id: str | None = None
    hint: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "is_valid": self.is_valid,
            "candidate_name": self.candidate_name,
        }
        if self.message:
            payload["message"] = self.message
        if self.conflict_group_id:
            payload["conflict_group_id"] = self.conflict_group_id
        if self.hint:
            payload["hint"] = self.hint
        return payload


@dataclass(frozen=True)
class ReviewActionValidationErrorResponseDTO:
    error: str
    message: str
    validation: ReviewValidationFeedbackDTO
    action_type: str
    group_id: str | None = None
    candidate_id: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error": self.error,
            "message": self.message,
            "validation": self.validation.to_payload(),
            "action": {
                "action_type": self.action_type,
            },
        }
        if self.group_id:
            payload["action"]["group_id"] = self.group_id
        if self.candidate_id:
            payload["action"]["candidate_id"] = self.candidate_id
        return payload


@dataclass(frozen=True)
class ReviewGroupResponseDTO:
    group_id: str
    display_name: str
    accepted_name: str | None
    accepted_name_summary: str | None
    is_collapsed: bool
    resolution_status: str
    rejected_candidate_ids: list[str]
    active_spellings: list[str]
    active_candidate_count: int
    total_candidate_count: int
    occurrence_count: int
    is_consensus: bool

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> ReviewGroupResponseDTO:
        group_id = str(payload.get("group_id", "")).strip()
        if not group_id:
            raise SchemaValidationError("group_id is required")
        accepted_name_raw = payload.get("accepted_name")
        accepted_name = str(accepted_name_raw).strip() if accepted_name_raw else None
        display_name = str(payload.get("display_name", "")).strip()
        active_spellings = [
            str(item).strip()
            for item in payload.get("active_spellings", [])
            if str(item).strip()
        ]
        active_candidate_count = int(payload.get("active_candidate_count", len(active_spellings)))
        total_candidate_count = int(payload.get("total_candidate_count", payload.get("occurrence_count", 0)))
        occurrence_count = int(payload.get("occurrence_count", total_candidate_count))
        resolution_status = str(payload.get("resolution_status", "UNRESOLVED"))
        accepted_name_summary_raw = payload.get("accepted_name_summary")
        accepted_name_summary = str(accepted_name_summary_raw).strip() if accepted_name_summary_raw else None
        if not accepted_name_summary:
            accepted_name_summary = accepted_name
        return ReviewGroupResponseDTO(
            group_id=group_id,
            display_name=display_name,
            accepted_name=accepted_name,
            accepted_name_summary=accepted_name_summary,
            is_collapsed=bool(payload.get("is_collapsed", False)),
            resolution_status=resolution_status,
            rejected_candidate_ids=[
                str(item)
                for item in payload.get("rejected_candidate_ids", [])
                if str(item).strip()
            ],
            active_spellings=active_spellings,
            active_candidate_count=active_candidate_count,
            total_candidate_count=total_candidate_count,
            occurrence_count=occurrence_count,
            is_consensus=bool(
                payload.get(
                    "is_consensus",
                    resolution_status == "RESOLVED" and (bool(accepted_name) or len(active_spellings) == 1),
                )
            ),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "display_name": self.display_name,
            "accepted_name": self.accepted_name,
            "accepted_name_summary": self.accepted_name_summary,
            "is_collapsed": self.is_collapsed,
            "resolution_status": self.resolution_status,
            "rejected_candidate_ids": list(self.rejected_candidate_ids),
            "active_spellings": list(self.active_spellings),
            "active_candidate_count": self.active_candidate_count,
            "total_candidate_count": self.total_candidate_count,
            "occurrence_count": self.occurrence_count,
            "is_consensus": self.is_consensus,
        }


@dataclass(frozen=True)
class ReviewHistoryRestoreRequestDTO:
    session_id: str
    create_restore_snapshot: bool = False

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> ReviewHistoryRestoreRequestDTO:
        session_id = str(payload.get("session_id", "")).strip()
        if not session_id:
            raise SchemaValidationError("session_id is required")
        create_restore_snapshot = bool(payload.get("create_restore_snapshot", False))
        return ReviewHistoryRestoreRequestDTO(
            session_id=session_id,
            create_restore_snapshot=create_restore_snapshot,
        )
