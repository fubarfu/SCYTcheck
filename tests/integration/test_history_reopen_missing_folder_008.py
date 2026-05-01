from __future__ import annotations

from pathlib import Path

from src.services.history_service import HistoryService
from src.web.app.history_store import HistoryStore


def test_validation_flow_e_missing_output_folder_warning_path(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    csv_path = output / "result.csv"
    csv_path.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,1\n", encoding="utf-8")

    service = HistoryService(store=HistoryStore(index_path=tmp_path / "video_history.json"))
    merged = service.merge_run(
        source_type="local_file",
        source_value=str(tmp_path / "video.mp4"),
        canonical_source=str(tmp_path / "video.mp4").lower(),
        duration_seconds=100,
        result_csv_path=str(csv_path),
        output_folder=str(output),
        context={
            "scan_region": {"x": 10, "y": 20, "width": 100, "height": 40},
            "context_patterns": [],
            "analysis_settings": {},
        },
    )

    output.rename(tmp_path / "out-renamed")
    reopen = service.reopen(merged["history_id"])
    assert reopen["history_id"] == merged["history_id"]
    assert reopen["derived_results"]["resolution_status"] == "missing_folder"
    assert reopen["review_route"].endswith(merged["history_id"])
