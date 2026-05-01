from __future__ import annotations

from src.services.history_service import HistoryService
from src.web.app.history_store import HistoryStore


def _merge(service: HistoryService, source: str, duration: int | None, csv_path: str, output: str) -> str:
    body = service.merge_run(
        source_type="youtube_url",
        source_value=f"https://youtube.com/watch?v={source}",
        canonical_source=f"youtube:{source}",
        duration_seconds=duration,
        result_csv_path=csv_path,
        output_folder=output,
        context={
            "scan_region": {"x": 1, "y": 1, "width": 10, "height": 10},
            "context_patterns": [],
            "analysis_settings": {},
        },
    )
    return str(body["history_id"])


def test_history_list_order_and_soft_delete_exclusion(tmp_path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    csv1 = output / "a.csv"
    csv2 = output / "b.csv"
    csv1.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nA,1\n", encoding="utf-8")
    csv2.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nB,2\n", encoding="utf-8")

    service = HistoryService(store=HistoryStore(index_path=tmp_path / "video_history.json"))
    first_id = _merge(service, "first", 10, str(csv1), str(output))
    second_id = _merge(service, "second", 20, str(csv2), str(output))

    listed = service.list_videos()
    assert listed["total"] == 2
    assert listed["items"][0]["history_id"] == second_id

    service.delete_video(first_id)
    listed_after_delete = service.list_videos()
    assert listed_after_delete["total"] == 1
    assert listed_after_delete["items"][0]["history_id"] == second_id
