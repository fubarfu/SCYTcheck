from __future__ import annotations

from pathlib import Path

from src.services.history_service import HistoryService
from src.web.app.history_store import HistoryStore


def test_validation_flow_b_deterministic_merge_and_run_count(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    csv1 = output / "run1.csv"
    csv2 = output / "run2.csv"
    csv1.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nA,1\n", encoding="utf-8")
    csv2.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nB,2\n", encoding="utf-8")

    service = HistoryService(store=HistoryStore(index_path=tmp_path / "video_history.json"))

    first = service.merge_run(
        source_type="youtube_url",
        source_value="https://youtube.com/watch?v=abc123",
        canonical_source="youtube:abc123",
        duration_seconds=300,
        result_csv_path=str(csv1),
        output_folder=str(output),
        context={"scan_region": {"x": 1, "y": 1, "width": 10, "height": 10}, "context_patterns": [], "analysis_settings": {}},
    )
    second = service.merge_run(
        source_type="youtube_url",
        source_value="https://youtube.com/watch?v=abc123",
        canonical_source="youtube:abc123",
        duration_seconds=300,
        result_csv_path=str(csv2),
        output_folder=str(output),
        context={"scan_region": {"x": 1, "y": 1, "width": 10, "height": 10}, "context_patterns": [], "analysis_settings": {}},
    )

    assert second["history_id"] == first["history_id"]
    assert second["run_count"] == 2
    listed = service.list_videos()
    assert listed["total"] == 1
