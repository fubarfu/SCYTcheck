from __future__ import annotations

from pathlib import Path

from src.services.history_service import HistoryService
from src.web.app.history_store import HistoryStore


def test_validation_flow_a_create_and_reopen_history_entry(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    csv_path = output / "result.csv"
    csv_path.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,1\n", encoding="utf-8")
    csv_path.with_suffix(".review.json").write_text("{}", encoding="utf-8")
    (output / "newer.csv").write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nBob,2\n",
        encoding="utf-8",
    )

    service = HistoryService(store=HistoryStore(index_path=tmp_path / "video_history.json"))
    merged = service.merge_run(
        source_type="youtube_url",
        source_value="https://youtube.com/watch?v=abc123",
        canonical_source="youtube:abc123",
        duration_seconds=100,
        result_csv_path=str(csv_path),
        output_folder=str(output),
        context={
            "scan_region": {"x": 10, "y": 20, "width": 100, "height": 40},
            "context_patterns": [{"id": "p1", "enabled": True}],
            "analysis_settings": {"ocr_confidence_threshold": 40},
        },
    )

    reopen = service.reopen(merged["history_id"])
    assert reopen["analysis_context"]["source_type"] == "youtube_url"
    assert reopen["analysis_context"]["source_value"] == "https://youtube.com/watch?v=abc123"
    assert reopen["analysis_context"]["scan_region"]["width"] == 100
    assert reopen["analysis_context"]["output_folder"] == str(output)
    assert reopen["derived_results"]["resolution_status"] == "ready"
    assert reopen["derived_results"]["primary_csv_path"] == str(csv_path)
    assert reopen["review_route"].endswith(merged["history_id"])
