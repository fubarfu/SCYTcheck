from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_history import ReviewHistoryHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.review_history_store import ReviewHistoryStore
from src.web.app.review_lock_service import ReviewLockService
from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.web.app.session_manager import SessionManager


def _make_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "review_history_contract_012.csv"
    csv_path.write_text(
        "#schema_version=1.0\n"
        "PlayerName,StartTimestamp\n"
        "Alice,00:00:01.000\n"
        "Alicia,00:00:01.250\n",
        encoding="utf-8",
    )
    return csv_path


def _bootstrap(tmp_path: Path) -> tuple[ReviewSessionHandler, ReviewActionsHandler, ReviewHistoryHandler, str, str, str]:
    manager = SessionManager()
    sidecar = ReviewSidecarStore()
    history_store = ReviewHistoryStore(sidecar)
    locks = ReviewLockService()

    sessions = ReviewSessionHandler(manager, lock_service=locks, history_store=history_store)
    actions = ReviewActionsHandler(manager, lock_service=locks, history_store=history_store)
    history = ReviewHistoryHandler(manager, history_store=history_store, lock_service=locks)

    load_status, load_body = sessions.post_load({"csv_path": str(_make_csv(tmp_path))})
    assert load_status == 200
    session_id = load_body["session_id"]
    video_id = load_body["workspace"]["video_id"]

    state = manager.get(session_id)
    assert state is not None
    session_status, session_payload = sessions.get_session(session_id)
    assert session_status == 200
    first_group = session_payload["groups"][0]
    candidate_id = first_group["candidates"][0]["candidate_id"]

    action_status, action_body = actions.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [candidate_id],
            "payload": {"group_id": first_group["group_id"]},
        },
    )
    assert action_status == 200
    history_entry_id = action_body["history_entry_id"]
    assert history_entry_id

    return sessions, actions, history, session_id, video_id, history_entry_id


def test_contract_get_history_list_and_entry_payload(tmp_path: Path) -> None:
    _, _, history, session_id, video_id, entry_id = _bootstrap(tmp_path)

    list_status, list_body = history.get_history(video_id, session_id=session_id)
    assert list_status == 200
    assert len(list_body["entries"]) >= 1

    entry_status, entry_body = history.get_history_entry(video_id, entry_id, session_id=session_id)
    assert entry_status == 200
    assert entry_body["entry_id"] == entry_id
    assert "snapshot" in entry_body


def test_contract_session_refresh_keeps_workspace_metadata(tmp_path: Path) -> None:
    sessions, _, _, session_id, video_id, _ = _bootstrap(tmp_path)

    session_status, session_body = sessions.get_session(session_id)
    assert session_status == 200
    assert session_body["workspace"]["video_id"] == video_id
    assert session_body["workspace"]["history_container_path"]


def test_contract_restore_creates_restore_snapshot(tmp_path: Path) -> None:
    sessions, _, history, session_id, video_id, entry_id = _bootstrap(tmp_path)

    restore_status, restore_body = history.post_restore(
        video_id,
        entry_id,
        {"session_id": session_id, "create_restore_snapshot": True},
    )
    assert restore_status == 200
    assert restore_body["status"] == "restored"
    assert restore_body["created_restore_entry_id"] is not None

    lock_status, lock_body = history.get_lock(video_id, session_id=session_id)
    assert lock_status == 200
    assert lock_body["readonly"] is False

    refreshed_status, refreshed_body = sessions.get_session(session_id)
    assert refreshed_status == 200
    assert isinstance(refreshed_body.get("groups", []), list)


def test_contract_second_session_mutation_returns_workspace_locked(tmp_path: Path) -> None:
    sessions, actions, history, owner_session_id, video_id, _ = _bootstrap(tmp_path)

    load_status, load_body = sessions.post_load({"csv_path": str(_make_csv(tmp_path))})
    assert load_status == 200
    viewer_session_id = load_body["session_id"]
    assert viewer_session_id != owner_session_id

    viewer_state_status, viewer_state = sessions.get_session(viewer_session_id)
    assert viewer_state_status == 200
    first_group = viewer_state["groups"][0]
    candidate_id = first_group["candidates"][0]["candidate_id"]

    action_status, action_body = actions.post_action(
        viewer_session_id,
        {
            "action_type": "confirm",
            "target_ids": [candidate_id],
            "payload": {"group_id": first_group["group_id"]},
        },
    )
    assert action_status == 409
    assert action_body["error"] == "workspace_locked"

    lock_status, lock_body = history.get_lock(video_id, session_id=viewer_session_id)
    assert lock_status == 200
    assert lock_body["readonly"] is True


# ---------------------------------------------------------------------------
# T029 - US3: reviewed_names in workspace and history payloads
# ---------------------------------------------------------------------------

def test_contract_reviewed_names_appear_in_workspace_response(tmp_path: Path) -> None:
    sessions, actions, history, session_id, video_id, _ = _bootstrap(tmp_path)

    workspace_status, workspace_body = history.get_workspace(video_id, session_id=session_id)
    assert workspace_status == 200
    reviewed = workspace_body.get("reviewed_names", [])
    assert isinstance(reviewed, list)
    assert len(reviewed) >= 1


def test_contract_reviewed_names_in_history_entry_snapshot(tmp_path: Path) -> None:
    _, _, history, session_id, video_id, entry_id = _bootstrap(tmp_path)

    entry_status, entry_body = history.get_history_entry(video_id, entry_id, session_id=session_id)
    assert entry_status == 200
    snapshot = entry_body.get("snapshot", {})
    reviewed = snapshot.get("reviewed_names", [])
    assert isinstance(reviewed, list)
    # At least one name was accepted during _bootstrap, so reviewed_names must not be empty
    assert len(reviewed) >= 1


# ---------------------------------------------------------------------------
# T017A - US1: first-save bootstrap contract (empty history on fresh workspace)
# ---------------------------------------------------------------------------

def test_contract_fresh_workspace_history_is_empty_before_first_action(tmp_path: Path) -> None:
    manager = SessionManager()
    sidecar = ReviewSidecarStore()
    history_store = ReviewHistoryStore(sidecar)
    locks = ReviewLockService()
    sessions = ReviewSessionHandler(manager, lock_service=locks, history_store=history_store)
    hist = ReviewHistoryHandler(manager, history_store=history_store, lock_service=locks)

    csv_path = tmp_path / "bootstrap_contract.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,00:00:01.000\n",
        encoding="utf-8",
    )
    load_status, load_body = sessions.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]
    video_id = load_body["workspace"]["video_id"]

    list_status, list_body = hist.get_history(video_id, session_id=session_id)
    assert list_status == 200
    assert list_body["entries"] == []
