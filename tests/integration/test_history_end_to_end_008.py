from __future__ import annotations

from pathlib import Path

from src.web.api.routes.history import HistoryHandler
from src.services.history_service import HistoryService
from src.web.app.history_store import HistoryStore
from tests.fixtures.history_008 import make_merge_payload


def test_end_to_end_feature_008_history_flow(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()

    handler = HistoryHandler(service=HistoryService(store=HistoryStore(index_path=tmp_path / "video_history.json")))

    merge_status, merge_body = handler.post_merge_run(
        make_merge_payload(
            source_type="youtube_url",
            source_value="https://youtube.com/watch?v=abc123",
            canonical_source="youtube:abc123",
            duration_seconds=120,
            output_folder=output,
        )
    )
    assert merge_status == 200

    list_status, list_body = handler.get_videos()
    assert list_status == 200
    assert list_body["total"] == 1

    reopen_status, reopen_body = handler.post_reopen({"history_id": merge_body["history_id"]})
    assert reopen_status == 200
    assert reopen_body["review_route"].startswith("/review")

    delete_status, _ = handler.delete_video(merge_body["history_id"])
    assert delete_status == 200

    list_status_after, list_body_after = handler.get_videos()
    assert list_status_after == 200
    assert list_body_after["total"] == 0
