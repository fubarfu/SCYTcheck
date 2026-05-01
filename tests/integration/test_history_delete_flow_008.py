from __future__ import annotations

from pathlib import Path

from src.services.history_service import HistoryService
from src.web.app.history_store import HistoryStore


def test_validation_flow_d_delete_removes_list_entry_not_files(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    csv_path = output / "result.csv"
    csv_path.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nA,1\n", encoding="utf-8")

    service = HistoryService(store=HistoryStore(index_path=tmp_path / "video_history.json"))
    merged = service.merge_run(
        source_type="local_file",
        source_value=str(tmp_path / "video.mp4"),
        canonical_source=str(tmp_path / "video.mp4").lower(),
        duration_seconds=100,
        result_csv_path=str(csv_path),
        output_folder=str(output),
        context={"scan_region": {"x": 1, "y": 1, "width": 10, "height": 10}, "context_patterns": [], "analysis_settings": {}},
    )

    service.delete_video(merged["history_id"])
    listed = service.list_videos()
    assert listed["total"] == 0
    assert csv_path.exists()
