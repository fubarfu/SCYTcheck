from __future__ import annotations

from pathlib import Path
from time import perf_counter

from src.services.history_service import HistoryService
from src.web.app.history_store import HistoryStore


def test_history_list_and_reopen_performance_targets(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()

    store = HistoryStore(index_path=tmp_path / "video_history.json")
    service = HistoryService(store=store)

    for index in range(50):
        csv_path = output / f"run_{index}.csv"
        csv_path.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nA,1\n", encoding="utf-8")
        service.merge_run(
            source_type="youtube_url",
            source_value=f"https://youtube.com/watch?v=id{index}",
            canonical_source=f"youtube:id{index}",
            duration_seconds=100 + index,
            result_csv_path=str(csv_path),
            output_folder=str(output),
            context={"scan_region": {"x": 1, "y": 1, "width": 10, "height": 10}, "context_patterns": [], "analysis_settings": {}},
        )

    list_start = perf_counter()
    listed = service.list_videos(limit=200)
    list_elapsed_ms = (perf_counter() - list_start) * 1000.0

    reopen_start = perf_counter()
    service.reopen(listed["items"][0]["history_id"])
    reopen_elapsed_sec = perf_counter() - reopen_start

    assert list_elapsed_ms <= 200.0
    assert reopen_elapsed_sec <= 5.0
