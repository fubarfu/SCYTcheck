from __future__ import annotations

from pathlib import Path

from src.web.app.review_history_store import ReviewHistoryStore


def _payload(name: str) -> dict:
    return {
        "groups": [
            {
                "group_id": "g1",
                "resolution_status": "RESOLVED",
                "accepted_name": name,
                "candidates": [{"candidate_id": "c1", "extracted_name": name}],
            }
        ],
        "accepted_names": {"g1": name},
    }


def test_restore_from_compressed_entry_is_deterministic(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    store = ReviewHistoryStore(max_uncompressed=1)
    first = store.append_snapshot(csv_path, _payload("Alice"), "confirm")
    store.append_snapshot(csv_path, _payload("Alicia"), "confirm")

    restored_payload, restore_entry_id = store.restore_snapshot(
        csv_path,
        _payload("Alicia"),
        first["entry_id"],
        create_restore_snapshot=True,
    )

    assert restored_payload["accepted_names"]["g1"] == "Alice"
    assert restore_entry_id is None
    remaining_entries = store.list_entries(csv_path, _payload("Alice"))
    assert [entry["entry_id"] for entry in remaining_entries] == [first["entry_id"]]


def test_restore_without_provenance_snapshot_keeps_state_only(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    store = ReviewHistoryStore(max_uncompressed=5)
    first = store.append_snapshot(csv_path, _payload("Alice"), "confirm")

    restored_payload, restore_entry_id = store.restore_snapshot(
        csv_path,
        _payload("Alicia"),
        first["entry_id"],
        create_restore_snapshot=False,
    )

    assert restored_payload["accepted_names"]["g1"] == "Alice"
    assert restore_entry_id is None


def test_restore_snapshot_deletes_newer_entries(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    store = ReviewHistoryStore(max_uncompressed=5)
    first = store.append_snapshot(csv_path, _payload("Alice"), "confirm")
    second = store.append_snapshot(csv_path, _payload("Alicia"), "confirm")
    third = store.append_snapshot(csv_path, _payload("Alise"), "confirm")

    restored_payload, restore_entry_id = store.restore_snapshot(
        csv_path,
        _payload("Alise"),
        first["entry_id"],
        create_restore_snapshot=False,
    )

    assert restored_payload["accepted_names"]["g1"] == "Alice"
    assert restore_entry_id is None
    remaining_entries = store.list_entries(csv_path, _payload("Alice"))
    assert [entry["entry_id"] for entry in remaining_entries] == [first["entry_id"]]
    assert second["entry_id"] not in {entry["entry_id"] for entry in remaining_entries}
    assert third["entry_id"] not in {entry["entry_id"] for entry in remaining_entries}


def test_restore_snapshot_rebuilds_candidate_statuses_from_snapshot(tmp_path: Path) -> None:
    csv_path = tmp_path / "restore_candidates.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    store = ReviewHistoryStore(max_uncompressed=5)
    first_payload = {
        "groups": [
            {
                "group_id": "g1",
                "resolution_status": "RESOLVED",
                "accepted_name": "Alice",
                "rejected_candidate_ids": ["c2"],
                "is_collapsed": True,
                "candidates": [
                    {"candidate_id": "c1", "extracted_name": "Alice", "status": "confirmed"},
                    {"candidate_id": "c2", "extracted_name": "Alicia", "status": "rejected"},
                ],
            },
            {
                "group_id": "g2",
                "resolution_status": "RESOLVED",
                "accepted_name": "Bob",
                "rejected_candidate_ids": [],
                "is_collapsed": True,
                "candidates": [
                    {"candidate_id": "c3", "extracted_name": "Bob", "status": "confirmed"},
                ],
            },
        ],
        "accepted_names": {"g1": "Alice", "g2": "Bob"},
        "candidates": [
            {"candidate_id": "c1", "extracted_name": "Alice", "status": "confirmed"},
            {"candidate_id": "c2", "extracted_name": "Alicia", "status": "rejected"},
            {"candidate_id": "c3", "extracted_name": "Bob", "status": "confirmed"},
        ],
    }
    first = store.append_snapshot(csv_path, first_payload, "confirm")

    current_payload = {
        "groups": [
            {
                "group_id": "g1",
                "resolution_status": "RESOLVED",
                "accepted_name": "Alice",
                "rejected_candidate_ids": ["c2"],
                "is_collapsed": True,
                "candidates": [
                    {"candidate_id": "c1", "extracted_name": "Alice", "status": "confirmed"},
                    {"candidate_id": "c2", "extracted_name": "Alicia", "status": "rejected"},
                ],
            },
            {
                "group_id": "g2",
                "resolution_status": "UNRESOLVED",
                "accepted_name": None,
                "rejected_candidate_ids": ["c3"],
                "is_collapsed": False,
                "candidates": [
                    {"candidate_id": "c3", "extracted_name": "Bob", "status": "rejected"},
                ],
            },
        ],
        "accepted_names": {"g1": "Alice"},
        "candidates": [
            {"candidate_id": "c1", "extracted_name": "Alice", "status": "confirmed"},
            {"candidate_id": "c2", "extracted_name": "Alicia", "status": "rejected"},
            {"candidate_id": "c3", "extracted_name": "Bob", "status": "rejected"},
        ],
        "rejected_candidates": {"g1": ["c2"], "g2": ["c3"]},
        "resolution_status": {"g1": "RESOLVED", "g2": "UNRESOLVED"},
    }

    restored_payload, _ = store.restore_snapshot(
        csv_path,
        current_payload,
        first["entry_id"],
        create_restore_snapshot=False,
    )

    restored_candidates = {item["candidate_id"]: item["status"] for item in restored_payload["candidates"]}
    assert restored_candidates["c1"] == "confirmed"
    assert restored_candidates["c2"] == "rejected"
    assert restored_candidates["c3"] == "confirmed"
    assert restored_payload["accepted_names"] == {"g1": "Alice", "g2": "Bob"}
    assert restored_payload["resolution_status"]["g2"] == "RESOLVED"


# ---------------------------------------------------------------------------
# T028 – US3: reviewed-name list durability across snapshots
# ---------------------------------------------------------------------------


def _payload_multi(names: list[str]) -> dict:
    groups = [
        {
            "group_id": f"g{i}",
            "resolution_status": "RESOLVED",
            "accepted_name": name,
            "candidates": [{"candidate_id": f"c{i}", "extracted_name": name}],
        }
        for i, name in enumerate(names)
    ]
    accepted = {f"g{i}": name for i, name in enumerate(names)}
    return {"groups": groups, "accepted_names": accepted}


def test_reviewed_names_are_persisted_in_snapshot(tmp_path: Path) -> None:
    csv_path = tmp_path / "names_test.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    store = ReviewHistoryStore(max_uncompressed=50)
    entry = store.append_snapshot(csv_path, _payload_multi(["Alice", "Bob"]), "confirm")

    snapshot = entry.get("snapshot", {})
    reviewed = snapshot.get("reviewed_names", [])
    assert "Alice" in reviewed
    assert "Bob" in reviewed


def test_restore_snapshot_preserves_reviewed_names(tmp_path: Path) -> None:
    csv_path = tmp_path / "names_test2.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    store = ReviewHistoryStore(max_uncompressed=5)
    first_entry = store.append_snapshot(csv_path, _payload_multi(["Alice", "Bob"]), "confirm")
    store.append_snapshot(csv_path, _payload_multi(["Charlie"]), "confirm")  # later state with different names

    restored, _ = store.restore_snapshot(
        csv_path,
        _payload_multi(["Charlie"]),
        first_entry["entry_id"],
        create_restore_snapshot=False,
    )

    # restored_payload should reflect the accepted_names from the first snapshot
    assert "Alice" in restored["accepted_names"].values()
    assert "Bob" in restored["accepted_names"].values()
    # reviewed_names must be in the restored state
    reviewed = restored.get("reviewed_names", [])
    assert "Alice" in reviewed
    assert "Bob" in reviewed
