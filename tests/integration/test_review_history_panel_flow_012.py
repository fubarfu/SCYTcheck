from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_history import ReviewHistoryHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.review_history_store import ReviewHistoryStore
from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.web.app.session_manager import SessionManager


def _csv(tmp_path: Path) -> Path:
    path = tmp_path / "review_history_integration_012.csv"
    path.write_text(
        "#schema_version=1.0\n"
        "PlayerName,StartTimestamp\n"
        "Alice,00:00:01.000\n"
        "Alicia,00:00:01.250\n",
        encoding="utf-8",
    )
    return path


def _other_csv(tmp_path: Path, name: str, player_name: str = "Bob") -> Path:
    path = tmp_path / name
    path.write_text(
        "#schema_version=1.0\n"
        f"PlayerName,StartTimestamp\n{player_name},00:00:02.000\n",
        encoding="utf-8",
    )
    return path


def _services() -> tuple[ReviewSessionHandler, ReviewActionsHandler, ReviewHistoryHandler]:
    manager = SessionManager()
    sidecar = ReviewSidecarStore()
    history_store = ReviewHistoryStore(sidecar)
    return (
        ReviewSessionHandler(manager, history_store=history_store),
        ReviewActionsHandler(manager, history_store=history_store),
        ReviewHistoryHandler(manager, history_store=history_store),
    )


def test_restore_flow_deletes_newer_snapshots_after_video_switch(tmp_path: Path) -> None:
    sessions, actions, history = _services()

    load_status, load_body = sessions.post_load({"csv_path": str(_csv(tmp_path))})
    assert load_status == 200
    session_id = load_body["session_id"]
    video_id = load_body["workspace"]["video_id"]

    session_status, session = sessions.get_session(session_id)
    assert session_status == 200
    first_group = session["groups"][0]
    candidate_id = first_group["candidates"][0]["candidate_id"]

    confirm_status, confirm_body = actions.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [candidate_id],
            "payload": {"group_id": first_group["group_id"]},
        },
    )
    assert confirm_status == 200
    assert confirm_body["history_entry_id"] is None

    switch_status, _ = sessions.post_load({"csv_path": str(_other_csv(tmp_path, "switch.csv"))})
    assert switch_status == 200

    before_restore_status, before_restore_body = history.get_history(video_id, session_id=session_id)
    assert before_restore_status == 200
    entry_id = before_restore_body["entries"][0]["entry_id"]

    restore_status, restore_body = history.post_restore(
        video_id,
        entry_id,
        {"session_id": session_id, "create_restore_snapshot": True},
    )
    assert restore_status == 200
    assert restore_body["created_restore_entry_id"] is None

    flush_status, _ = sessions.post_load({"csv_path": str(_other_csv(tmp_path, "flush_after_restore.csv", player_name="Carol"))})
    assert flush_status == 200

    list_status, list_body = history.get_history(video_id, session_id=session_id)
    assert list_status == 200
    assert len(list_body["entries"]) == 2
    assert list_body["entries"][1]["entry_id"] == entry_id


def test_non_state_mutation_does_not_create_snapshot(tmp_path: Path) -> None:
    sessions, actions, history = _services()

    load_status, load_body = sessions.post_load({"csv_path": str(_csv(tmp_path))})
    assert load_status == 200
    session_id = load_body["session_id"]
    video_id = load_body["workspace"]["video_id"]

    before_status, before = history.get_history(video_id, session_id=session_id)
    assert before_status == 200
    before_count = len(before["entries"])

    session_status, session = sessions.get_session(session_id)
    assert session_status == 200
    group_id = session["groups"][0]["group_id"]

    toggle_status, toggle_body = actions.post_action(
        session_id,
        {
            "action_type": "toggle_collapse",
            "target_ids": [],
            "payload": {"group_id": group_id, "is_collapsed": False},
        },
    )
    assert toggle_status == 200
    assert toggle_body["history_entry_id"] is None

    after_status, after = history.get_history(video_id, session_id=session_id)
    assert after_status == 200
    assert len(after["entries"]) == before_count


# ---------------------------------------------------------------------------
# T024 - US2: workspace isolation (different csv files -> different video_ids)
# ---------------------------------------------------------------------------

def test_two_different_csv_files_produce_separate_workspaces(tmp_path: Path) -> None:
    sessions, actions, history = _services()

    csv_a = tmp_path / "review_a.csv"
    csv_a.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,00:00:01.000\n",
        encoding="utf-8",
    )
    csv_b = tmp_path / "review_b.csv"
    csv_b.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nBob,00:00:02.000\n",
        encoding="utf-8",
    )

    load_a_status, load_a = sessions.post_load({"csv_path": str(csv_a)})
    assert load_a_status == 200
    video_id_a = load_a["workspace"]["video_id"]

    load_b_status, load_b = sessions.post_load({"csv_path": str(csv_b)})
    assert load_b_status == 200
    video_id_b = load_b["workspace"]["video_id"]

    assert video_id_a != video_id_b


def test_same_csv_reopened_reuses_same_video_id(tmp_path: Path) -> None:
    sessions, _, _ = _services()

    csv_path = tmp_path / "review_reopen.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,00:00:01.000\n",
        encoding="utf-8",
    )

    load_1_status, load_1 = sessions.post_load({"csv_path": str(csv_path)})
    assert load_1_status == 200
    video_id_1 = load_1["workspace"]["video_id"]

    load_2_status, load_2 = sessions.post_load({"csv_path": str(csv_path)})
    assert load_2_status == 200
    video_id_2 = load_2["workspace"]["video_id"]

    assert video_id_1 == video_id_2


# ---------------------------------------------------------------------------
# T017A - US1: first-save history bootstrap on empty workspace
# ---------------------------------------------------------------------------

def test_first_action_bootstraps_history_after_switching_away_from_empty_workspace(tmp_path: Path) -> None:
    sessions, actions, history = _services()

    csv_path = tmp_path / "review_bootstrap.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,00:00:01.000\n",
        encoding="utf-8",
    )

    load_status, load_body = sessions.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]
    video_id = load_body["workspace"]["video_id"]

    before_status, before_body = history.get_history(video_id, session_id=session_id)
    assert before_status == 200
    assert len(before_body["entries"]) == 0

    session_status, session = sessions.get_session(session_id)
    assert session_status == 200
    first_group = session["groups"][0]
    candidate_id = first_group["candidates"][0]["candidate_id"]

    confirm_status, _ = actions.post_action(
        session_id,
        {"action_type": "confirm", "target_ids": [candidate_id], "payload": {"group_id": first_group["group_id"]}},
    )
    assert confirm_status == 200

    flush_status, _ = sessions.post_load({"csv_path": str(_other_csv(tmp_path, "bootstrap_flush.csv"))})
    assert flush_status == 200

    after_status, after_body = history.get_history(video_id, session_id=session_id)
    assert after_status == 200
    assert len(after_body["entries"]) == 1


def test_browser_close_flush_creates_entry_only_when_different_from_latest(tmp_path: Path) -> None:
    sessions, actions, history = _services()

    load_status, load_body = sessions.post_load({"csv_path": str(_csv(tmp_path))})
    assert load_status == 200
    session_id = load_body["session_id"]
    video_id = load_body["workspace"]["video_id"]

    session_status, session = sessions.get_session(session_id)
    assert session_status == 200
    first_group = session["groups"][0]
    candidate_id = first_group["candidates"][0]["candidate_id"]

    confirm_status, _ = actions.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [candidate_id],
            "payload": {"group_id": first_group["group_id"]},
        },
    )
    assert confirm_status == 200

    first_flush_status, first_flush = sessions.post_flush_on_close(session_id)
    assert first_flush_status == 200
    assert first_flush["flushed"] is True
    assert first_flush["reason"] == "flushed"

    second_flush_status, second_flush = sessions.post_flush_on_close(session_id)
    assert second_flush_status == 200
    assert second_flush["flushed"] is True
    assert second_flush["reason"] == "flushed"

    list_status, list_body = history.get_history(video_id, session_id=session_id)
    assert list_status == 200
    assert len(list_body["entries"]) == 2


def test_browser_close_flush_without_edits_creates_snapshot(tmp_path: Path) -> None:
    sessions, _, history = _services()

    load_status, load_body = sessions.post_load({"csv_path": str(_csv(tmp_path))})
    assert load_status == 200
    session_id = load_body["session_id"]
    video_id = load_body["workspace"]["video_id"]

    before_status, before_body = history.get_history(video_id, session_id=session_id)
    assert before_status == 200
    assert len(before_body["entries"]) == 0

    close_status, close_body = sessions.post_flush_on_close(session_id)
    assert close_status == 200
    assert close_body["flushed"] is True
    assert close_body["reason"] == "flushed"

    after_status, after_body = history.get_history(video_id, session_id=session_id)
    assert after_status == 200
    assert len(after_body["entries"]) == 1


def test_browser_close_flush_creates_entry_even_when_state_matches_latest_entry(tmp_path: Path) -> None:
    sessions, actions, history = _services()

    load_status, load_body = sessions.post_load({"csv_path": str(_csv(tmp_path))})
    assert load_status == 200
    session_id = load_body["session_id"]
    video_id = load_body["workspace"]["video_id"]

    session_status, session = sessions.get_session(session_id)
    assert session_status == 200
    first_group = session["groups"][0]
    candidate_id = first_group["candidates"][0]["candidate_id"]

    confirm_status, _ = actions.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [candidate_id],
            "payload": {"group_id": first_group["group_id"]},
        },
    )
    assert confirm_status == 200

    switch_status, _ = sessions.post_load({"csv_path": str(_other_csv(tmp_path, "switch_for_seed.csv"))})
    assert switch_status == 200

    switch_back_status, _ = sessions.post_load({"csv_path": str(_csv(tmp_path))})
    assert switch_back_status == 200

    close_status, close_body = sessions.post_flush_on_close(session_id)
    assert close_status == 200
    assert close_body["flushed"] is True
    assert close_body["reason"] == "flushed"

    list_status, list_body = history.get_history(video_id, session_id=session_id)
    assert list_status == 200
    assert len(list_body["entries"]) == 2


def test_video_switch_flush_creates_entry_even_when_state_matches_latest_entry(tmp_path: Path) -> None:
    sessions, actions, history = _services()

    base_csv = _csv(tmp_path)
    load_status, load_body = sessions.post_load({"csv_path": str(base_csv)})
    assert load_status == 200
    session_id = load_body["session_id"]
    video_id = load_body["workspace"]["video_id"]

    session_status, session = sessions.get_session(session_id)
    assert session_status == 200
    first_group = session["groups"][0]
    candidate_id = first_group["candidates"][0]["candidate_id"]

    confirm_status, _ = actions.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [candidate_id],
            "payload": {"group_id": first_group["group_id"]},
        },
    )
    assert confirm_status == 200

    switch_status, _ = sessions.post_load({"csv_path": str(_other_csv(tmp_path, "switch_seed.csv"))})
    assert switch_status == 200

    seed_status, seed_history = history.get_history(video_id, session_id=session_id)
    assert seed_status == 200
    assert len(seed_history["entries"]) == 1

    switch_back_status, _ = sessions.post_load({"csv_path": str(base_csv)})
    assert switch_back_status == 200

    second_switch_status, _ = sessions.post_load({"csv_path": str(_other_csv(tmp_path, "switch_again.csv", player_name="Carol"))})
    assert second_switch_status == 200

    final_status, final_history = history.get_history(video_id, session_id=session_id)
    assert final_status == 200
    assert len(final_history["entries"]) == 2


# ---------------------------------------------------------------------------
# T027A/T027B - US2: per-video settings round-trip via sidecar
# ---------------------------------------------------------------------------

def test_sidecar_persists_analysis_and_grouping_settings_atomically(tmp_path: Path) -> None:
    """Sidecar atomic save must preserve analysis_settings, grouping_settings, and scan_region
    so they can be read back unchanged on the next load (FR-006, FR-007)."""
    from src.web.app.review_sidecar_store import ReviewSidecarStore as _SidecarStore

    csv_path = tmp_path / "review_settings2.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,00:00:01.000\n",
        encoding="utf-8",
    )

    sidecar = _SidecarStore()
    payload = {
        "groups": [],
        "accepted_names": {},
        "analysis_settings": {"fps": 2, "confidence_threshold": 0.85},
        "grouping_settings": {"similarity_threshold": 0.75, "algorithm": "fuzzy"},
        "scan_region": {"x": 10, "y": 20, "width": 640, "height": 100},
    }
    sidecar.save(csv_path, payload)
    reloaded = sidecar.load(csv_path)

    assert reloaded is not None
    assert reloaded["analysis_settings"]["fps"] == 2
    assert reloaded["analysis_settings"]["confidence_threshold"] == 0.85
    assert reloaded["grouping_settings"]["algorithm"] == "fuzzy"
    assert reloaded["grouping_settings"]["similarity_threshold"] == 0.75
    assert reloaded["scan_region"]["width"] == 640
    assert reloaded["scan_region"]["x"] == 10


# ---------------------------------------------------------------------------
# T041 - Performance: restore UI feedback and hydration time at 100/500/1000 entries
# ---------------------------------------------------------------------------

import time


def _append_n_snapshots(store: ReviewHistoryStore, csv_path: Path, count: int) -> None:
    payload = {
        "groups": [{"group_id": "g1", "resolution_status": "RESOLVED", "accepted_name": "Alice"}],
        "accepted_names": {"g1": "Alice"},
    }
    for _ in range(count):
        store.append_snapshot(csv_path, payload, "confirm")


def test_list_entries_performance_100(tmp_path: Path) -> None:
    csv_path = tmp_path / "perf100.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")
    store = ReviewHistoryStore(max_uncompressed=20)
    payload = {"groups": [], "accepted_names": {}}
    _append_n_snapshots(store, csv_path, 100)

    t0 = time.monotonic()
    entries = store.list_entries(csv_path, payload)
    elapsed = time.monotonic() - t0

    assert len(entries) == 100
    assert elapsed < 2.0, f"list_entries for 100 entries took {elapsed:.2f}s (limit: 2s)"


def test_list_entries_performance_500(tmp_path: Path) -> None:
    csv_path = tmp_path / "perf500.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")
    store = ReviewHistoryStore(max_uncompressed=20)
    payload = {"groups": [], "accepted_names": {}}
    _append_n_snapshots(store, csv_path, 500)

    t0 = time.monotonic()
    entries = store.list_entries(csv_path, payload)
    elapsed = time.monotonic() - t0

    assert len(entries) == 500
    assert elapsed < 5.0, f"list_entries for 500 entries took {elapsed:.2f}s (limit: 5s)"


def test_list_entries_performance_1000(tmp_path: Path) -> None:
    csv_path = tmp_path / "perf1000.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")
    store = ReviewHistoryStore(max_uncompressed=20)
    payload = {"groups": [], "accepted_names": {}}
    _append_n_snapshots(store, csv_path, 1000)

    t0 = time.monotonic()
    entries = store.list_entries(csv_path, payload)
    elapsed = time.monotonic() - t0

    assert len(entries) == 1000
    assert elapsed < 10.0, f"list_entries for 1000 entries took {elapsed:.2f}s (limit: 10s)"
