from __future__ import annotations

from pathlib import Path

from src.web.api.routes.history import HistoryHandler
from src.services.history_service import HistoryService
from src.web.app.history_store import HistoryStore
from tests.fixtures.history_008 import make_merge_payload


def test_history_management_list_delete_reopen_journey(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()

    handler = HistoryHandler(service=HistoryService(store=HistoryStore(index_path=tmp_path / "video_history.json")))

    first_status, first_body = handler.post_merge_run(
        make_merge_payload(
            source_type="youtube_url",
            source_value="https://youtube.com/watch?v=aaa111",
            canonical_source="youtube:aaa111",
            duration_seconds=120,
            output_folder=output,
            csv_name="a.csv",
        )
    )
    second_status, second_body = handler.post_merge_run(
        make_merge_payload(
            source_type="youtube_url",
            source_value="https://youtube.com/watch?v=bbb222",
            canonical_source="youtube:bbb222",
            duration_seconds=220,
            output_folder=output,
            csv_name="b.csv",
        )
    )
    assert first_status == 200
    assert second_status == 200

    list_status, list_body = handler.get_videos()
    assert list_status == 200
    assert list_body["total"] == 2

    reopen_status, reopen_body = handler.post_reopen({"history_id": first_body["history_id"]})
    assert reopen_status == 200
    assert reopen_body["history_id"] == first_body["history_id"]

    delete_status, _ = handler.delete_video(second_body["history_id"])
    assert delete_status == 200

    list_status_after, list_body_after = handler.get_videos()
    assert list_status_after == 200
    assert list_body_after["total"] == 1
