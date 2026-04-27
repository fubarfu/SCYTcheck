from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_history import ReviewHistoryHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.review_history_store import ReviewHistoryStore
from src.web.app.review_lock_service import ReviewLockService
from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.web.app.session_manager import SessionManager


def _csv(tmp_path: Path) -> Path:
    path = tmp_path / "review_lock_integration_012.csv"
    path.write_text(
        "#schema_version=1.0\n"
        "PlayerName,StartTimestamp\n"
        "Alice,00:00:01.000\n"
        "Alicia,00:00:01.250\n",
        encoding="utf-8",
    )
    return path


def test_second_session_is_readonly_but_can_inspect_history(tmp_path: Path) -> None:
    manager = SessionManager()
    sidecar = ReviewSidecarStore()
    history_store = ReviewHistoryStore(sidecar)
    locks = ReviewLockService()

    sessions = ReviewSessionHandler(manager, lock_service=locks, history_store=history_store)
    actions = ReviewActionsHandler(manager, lock_service=locks, history_store=history_store)
    history = ReviewHistoryHandler(manager, history_store=history_store, lock_service=locks)

    load_owner_status, load_owner = sessions.post_load({"csv_path": str(_csv(tmp_path))})
    assert load_owner_status == 200
    owner_session_id = load_owner["session_id"]
    video_id = load_owner["workspace"]["video_id"]

    owner_state_status, owner_state = sessions.get_session(owner_session_id)
    assert owner_state_status == 200
    first_group = owner_state["groups"][0]
    candidate_id = first_group["candidates"][0]["candidate_id"]

    action_status, _ = actions.post_action(
        owner_session_id,
        {
            "action_type": "confirm",
            "target_ids": [candidate_id],
            "payload": {"group_id": first_group["group_id"]},
        },
    )
    assert action_status == 200

    load_viewer_status, load_viewer = sessions.post_load({"csv_path": str(_csv(tmp_path))})
    assert load_viewer_status == 200
    viewer_session_id = load_viewer["session_id"]
    assert load_viewer["readonly"] is True

    lock_status, lock = history.get_lock(video_id, session_id=viewer_session_id)
    assert lock_status == 200
    assert lock["readonly"] is True

    history_status, history_body = history.get_history(video_id, session_id=viewer_session_id)
    assert history_status == 200
    assert len(history_body["entries"]) >= 1
