from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
        output_folder = str(payload.get("output_folder", "")).strip()
        output_filename = str(payload.get("output_filename", "")).strip()

        if source_type not in {"youtube_url", "local_file"}:
            raise SchemaValidationError("source_type must be 'youtube_url' or 'local_file'")
        if not source_value:
            raise SchemaValidationError("source_value is required")
        if not output_folder:
            raise SchemaValidationError("output_folder is required")
        if not output_filename:
            raise SchemaValidationError("output_filename is required")

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
