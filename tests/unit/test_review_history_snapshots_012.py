from __future__ import annotations

from pathlib import Path

from src.web.app.review_history_store import ReviewHistoryStore
from src.web.app.review_mutation_service import should_create_snapshot_for_action


def _payload() -> dict:
    return {
        "groups": [
            {"group_id": "g1", "resolution_status": "RESOLVED", "accepted_name": "Alice"},
            {"group_id": "g2", "resolution_status": "UNRESOLVED", "accepted_name": None},
        ],
        "accepted_names": {"g1": "Alice"},
    }


def test_append_only_snapshots_preserve_order(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    store = ReviewHistoryStore(max_uncompressed=50)
    first = store.append_snapshot(csv_path, _payload(), "confirm")
    second = store.append_snapshot(csv_path, _payload(), "reject")

    entries = store.list_entries(csv_path, _payload())
    assert len(entries) == 2
    assert entries[0]["entry_id"] == second["entry_id"]
    assert entries[1]["entry_id"] == first["entry_id"]


def test_compaction_marks_older_entries_without_deleting(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    store = ReviewHistoryStore(max_uncompressed=2)
    for trigger in ["confirm", "reject", "unreject", "confirm"]:
        store.append_snapshot(csv_path, _payload(), trigger)

    entries = store.list_entries(csv_path, _payload())
    assert len(entries) == 4
    compressed_count = sum(1 for entry in entries if entry.get("compressed"))
    assert compressed_count >= 2


def test_snapshot_trigger_matrix_allows_only_state_changes() -> None:
    assert should_create_snapshot_for_action("confirm") is True
    assert should_create_snapshot_for_action("merge_groups") is True
    assert should_create_snapshot_for_action("toggle_collapse") is False


# ---------------------------------------------------------------------------
# T023 – US2: stable video_id folder identity
# ---------------------------------------------------------------------------

from src.web.app.review_sidecar_store import ReviewSidecarStore  # noqa: E402


def test_make_video_id_is_stable_across_calls() -> None:
    """Same source hint must always produce the same video_id."""
    store = ReviewSidecarStore()
    vid1 = store.make_video_id("https://youtube.com/watch?v=abc123")
    vid2 = store.make_video_id("https://youtube.com/watch?v=abc123")
    assert vid1 == vid2
    assert vid1.startswith("vid_")


def test_make_video_id_differs_for_different_sources() -> None:
    store = ReviewSidecarStore()
    vid1 = store.make_video_id("https://youtube.com/watch?v=abc123")
    vid2 = store.make_video_id("https://youtube.com/watch?v=xyz999")
    assert vid1 != vid2


def test_ensure_workspace_metadata_embeds_stable_video_id(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    store = ReviewSidecarStore()
    payload = {"source_value": "https://youtube.com/watch?v=abc123"}
    result1 = store.ensure_workspace_metadata(csv_path, payload)
    result2 = store.ensure_workspace_metadata(csv_path, payload)

    workspace1 = result1["workspace"]
    workspace2 = result2["workspace"]
    assert workspace1["video_id"] == workspace2["video_id"]
    assert workspace1["video_id"].startswith("vid_")
    assert "history_container_path" in workspace1
    assert "workspace_path" in workspace1


def test_ensure_workspace_metadata_preserves_existing_video_id(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    store = ReviewSidecarStore()
    payload = {
        "source_value": "https://youtube.com/watch?v=abc123",
        "workspace": {"video_id": "vid_existing_id_001", "display_title": "My Custom Title"},
    }
    result = store.ensure_workspace_metadata(csv_path, payload)
    assert result["workspace"]["video_id"] == "vid_existing_id_001"
    assert result["workspace"]["display_title"] == "My Custom Title"
