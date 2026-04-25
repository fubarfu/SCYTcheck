from __future__ import annotations

from src.web.api.schemas import (
    AnalysisStartRequestDTO,
    ReviewLoadRequestDTO,
    ScanRegionDTO,
    SchemaValidationError,
)
from src.web.app.settings_store import SettingsStore


def test_scan_region_dto_valid() -> None:
    payload = {"x": 100, "y": 50, "width": 200, "height": 60}
    dto = ScanRegionDTO.from_payload(payload)
    assert dto.x == 100
    assert dto.width == 200


def test_scan_region_dto_rejects_zero_dimensions() -> None:
    import pytest

    with pytest.raises(SchemaValidationError, match="positive"):
        ScanRegionDTO.from_payload({"x": 0, "y": 0, "width": 0, "height": 60})


def test_analysis_start_request_dto_valid() -> None:
    payload = {
        "source_type": "local_file",
        "source_value": "C:/videos/match.mp4",
        "output_folder": "C:/output",
        "output_filename": "match.csv",
        "scan_region": {"x": 10, "y": 20, "width": 100, "height": 40},
    }
    dto = AnalysisStartRequestDTO.from_payload(payload)
    assert dto.source_type == "local_file"
    assert len(dto.scan_regions) == 1
    assert dto.scan_regions[0].height == 40


def test_analysis_start_request_dto_accepts_multiple_regions() -> None:
    payload = {
        "source_type": "local_file",
        "source_value": "C:/videos/match.mp4",
        "output_folder": "C:/output",
        "output_filename": "match.csv",
        "scan_regions": [
            {"x": 10, "y": 20, "width": 100, "height": 40},
            {"x": 20, "y": 90, "width": 120, "height": 45},
        ],
    }
    dto = AnalysisStartRequestDTO.from_payload(payload)
    assert len(dto.scan_regions) == 2
    assert dto.scan_regions[1].y == 90


def test_analysis_start_request_dto_rejects_invalid_source_type() -> None:
    import pytest

    with pytest.raises(SchemaValidationError, match="source_type"):
        AnalysisStartRequestDTO.from_payload(
            {
                "source_type": "ftp",
                "source_value": "ftp://example.com",
                "output_folder": "C:/out",
                "output_filename": "test.csv",
                "scan_region": {"x": 0, "y": 0, "width": 10, "height": 10},
            }
        )


def test_review_load_request_dto_valid() -> None:
    dto = ReviewLoadRequestDTO.from_payload({"csv_path": "C:/output/result.csv"})
    assert dto.csv_path.suffix == ".csv"


def test_review_load_request_dto_rejects_non_csv() -> None:
    import pytest

    with pytest.raises(SchemaValidationError, match="csv"):
        ReviewLoadRequestDTO.from_payload({"csv_path": "C:/output/result.txt"})


def test_settings_store_load_returns_effective_analysis_defaults(tmp_path) -> None:
    store = SettingsStore(settings_path=tmp_path / "settings.json")

    loaded = store.load()

    assert loaded["filter_non_matching"] is True
    assert loaded["gating_enabled"] is False
    assert loaded["video_quality"] == "best"
    assert loaded["context_patterns"]
