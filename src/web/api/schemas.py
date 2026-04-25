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
