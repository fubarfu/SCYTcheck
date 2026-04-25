from __future__ import annotations

from pathlib import Path

from src.services.history_service import HistoryService
from src.web.api.routes.history import HistoryHandler
from src.web.app.history_store import HistoryStore
from tests.fixtures.history_008 import make_merge_payload


def _handler(tmp_path: Path) -> HistoryHandler:
    store = HistoryStore(index_path=tmp_path / "video_history.json")
    return HistoryHandler(service=HistoryService(store=store))


def test_get_history_videos_initially_empty(tmp_path: Path) -> None:
    handler = _handler(tmp_path)
    status, body = handler.get_videos()
    assert status == 200
    assert body["items"] == []
    assert body["total"] == 0


def test_post_merge_run_contract_behavior(tmp_path: Path) -> None:
    handler = _handler(tmp_path)
    output = tmp_path / "out"
    output.mkdir()

    payload = make_merge_payload(
        source_type="youtube_url",
        source_value="https://youtube.com/watch?v=abc123",
        canonical_source="youtube:abc123",
        duration_seconds=120,
        output_folder=output,
    )
    status, body = handler.post_merge_run(payload)
    assert status == 200
    assert body["merged"] is False
    assert body["run_count"] == 1

    payload["result_csv_path"] = str(output / "result_2.csv")
    (output / "result_2.csv").write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nBob,2\n", encoding="utf-8"
    )
    status_2, body_2 = handler.post_merge_run(payload)
    assert status_2 == 200
    assert body_2["merged"] is True
    assert body_2["run_count"] == 2


def test_post_merge_run_missing_duration_flags_potential_duplicate(tmp_path: Path) -> None:
    handler = _handler(tmp_path)
    output = tmp_path / "out"
    output.mkdir()

    payload = make_merge_payload(
        source_type="local_file",
        source_value=str(tmp_path / "video.mp4"),
        canonical_source=str(tmp_path / "video.mp4").lower(),
        duration_seconds=None,
        output_folder=output,
    )
    status, body = handler.post_merge_run(payload)
    assert status == 200
    assert body["potential_duplicate"] is True


def test_reopen_and_get_video_contract(tmp_path: Path) -> None:
    handler = _handler(tmp_path)
    output = tmp_path / "out"
    output.mkdir()

    payload = make_merge_payload(
        source_type="youtube_url",
        source_value="https://youtube.com/watch?v=abc123",
        canonical_source="youtube:abc123",
        duration_seconds=120,
        output_folder=output,
    )
    merge_status, merge_body = handler.post_merge_run(payload)
    assert merge_status == 200

    history_id = merge_body["history_id"]
    get_status, get_body = handler.get_video(history_id)
    assert get_status == 200
    assert get_body["history_id"] == history_id

    reopen_status, reopen_body = handler.post_reopen({"history_id": history_id})
    assert reopen_status == 200
    assert reopen_body["review_route"] == f"/review?history_id={history_id}"
    assert reopen_body["derived_results"]["resolution_status"] in {
        "ready",
        "partial",
        "missing_results",
        "missing_folder",
    }


def test_reopen_missing_folder_still_returns_metadata(tmp_path: Path) -> None:
    handler = _handler(tmp_path)
    output = tmp_path / "out"
    output.mkdir()

    payload = make_merge_payload(
        source_type="youtube_url",
        source_value="https://youtube.com/watch?v=abc123",
        canonical_source="youtube:abc123",
        duration_seconds=120,
        output_folder=output,
    )
    merge_status, merge_body = handler.post_merge_run(payload)
    assert merge_status == 200

    history_id = merge_body["history_id"]
    output.rename(tmp_path / "out-moved")

    reopen_status, reopen_body = handler.post_reopen({"history_id": history_id})
    assert reopen_status == 200
    assert reopen_body["history_id"] == history_id
    assert reopen_body["derived_results"]["resolution_status"] == "missing_folder"
    assert reopen_body["review_route"] == f"/review?history_id={history_id}"


def test_delete_history_entry_contract(tmp_path: Path) -> None:
    handler = _handler(tmp_path)
    output = tmp_path / "out"
    output.mkdir()

    payload = make_merge_payload(
        source_type="youtube_url",
        source_value="https://youtube.com/watch?v=abc123",
        canonical_source="youtube:abc123",
        duration_seconds=120,
        output_folder=output,
    )
    merge_status, merge_body = handler.post_merge_run(payload)
    assert merge_status == 200

    history_id = merge_body["history_id"]
    delete_status, delete_body = handler.delete_video(history_id)
    assert delete_status == 200
    assert delete_body == {"history_id": history_id, "deleted": True}

    list_status, list_body = handler.get_videos()
    assert list_status == 200
    assert list_body["total"] == 0
