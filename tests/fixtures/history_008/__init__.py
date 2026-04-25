from __future__ import annotations

from pathlib import Path
from typing import Any


def make_history_context(output_folder: Path) -> dict[str, Any]:
    return {
        "scan_region": {"x": 120, "y": 40, "width": 480, "height": 60},
        "context_patterns": [
            {
                "id": "default-has-joined",
                "before_text": None,
                "after_text": "has joined",
                "enabled": True,
            }
        ],
        "analysis_settings": {
            "ocr_confidence_threshold": 40,
            "tolerance_value": 0.75,
            "event_gap_threshold_sec": 1.0,
            "gating_enabled": False,
            "gating_threshold": 0.02,
            "video_quality": "best",
            "filter_non_matching": True,
            "logging_enabled": False,
        },
        "output_folder": str(output_folder),
    }


def make_merge_payload(
    *,
    source_type: str,
    source_value: str,
    canonical_source: str,
    duration_seconds: int | None,
    output_folder: Path,
    csv_name: str = "result.csv",
) -> dict[str, Any]:
    csv_path = output_folder / csv_name
    if not csv_path.exists():
        csv_path.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,1\n", encoding="utf-8")

    context = make_history_context(output_folder)
    return {
        "source_type": source_type,
        "source_value": source_value,
        "canonical_source": canonical_source,
        "duration_seconds": duration_seconds,
        "result_csv_path": str(csv_path),
        "output_folder": str(output_folder),
        "context": {
            "scan_region": context["scan_region"],
            "context_patterns": context["context_patterns"],
            "analysis_settings": context["analysis_settings"],
        },
    }
