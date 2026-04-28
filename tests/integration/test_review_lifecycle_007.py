from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.session_manager import SessionManager


def _setup_session(tmp_path: Path) -> tuple[str, SessionManager]:
    csv_path = tmp_path / "match.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,5.0\n", encoding="utf-8"
    )
    manager = SessionManager()
    handler = ReviewSessionHandler(session_manager=manager)
    _, body = handler.post_load({"csv_path": str(csv_path)})
    session_id = body["session_id"]

    state = manager.get(session_id)
    assert state is not None
    payload = dict(state.payload or {})
    candidate = {"candidate_id": "c001", "extracted_name": "Alice", "status": "pending"}
    payload["candidates"] = [candidate]
    payload["candidates_original"] = [candidate]
    manager.upsert(session_id, state.csv_path, payload)
    return session_id, manager


def test_lifecycle_confirm_persist_reload(tmp_path: Path) -> None:
    session_id, manager = _setup_session(tmp_path)
    actions = ReviewActionsHandler(session_manager=manager)
    status, body = actions.post_action(
        session_id, {"action_type": "confirm", "target_ids": ["c001"]}
    )
    assert status == 200
    assert body["persisted"] is True

    state = manager.get(session_id)
    assert state is not None
    assert state.payload["candidates"][0]["status"] == "confirmed"

    # Check review state was written into the per-video workspace
    workspace_path = Path(state.payload["workspace"]["workspace_path"])
    sidecar_path = workspace_path / "review_state.json"
    assert sidecar_path.exists()


def test_lifecycle_edit_then_undo(tmp_path: Path) -> None:
    session_id, manager = _setup_session(tmp_path)
    actions = ReviewActionsHandler(session_manager=manager)

    actions.post_action(
        session_id,
        {
            "action_type": "edit",
            "target_ids": ["c001"],
            "payload": {"corrected_text": "AliceEdited"},
        },
    )

    state = manager.get(session_id)
    assert state is not None
    assert state.payload["candidates"][0]["corrected_text"] == "AliceEdited"

    undo_status, undo_body = actions.post_undo(session_id)
    assert undo_status == 200
    assert undo_body["remaining_undo_count"] == 0

    state = manager.get(session_id)
    assert state is not None
    # After undo, original state restored
    assert state.payload["candidates"][0].get("corrected_text") is None
