from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.session_manager import SessionManager


def _make_valid_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "result.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,10.0\nBob,20.0\n",
        encoding="utf-8",
    )
    return csv_path


def test_review_session_load_rejects_missing_file(tmp_path: Path) -> None:
    handler = ReviewSessionHandler()
    status, body = handler.post_load({"csv_path": str(tmp_path / "missing.csv")})
    assert status == 404


def test_review_session_load_rejects_invalid_schema(tmp_path: Path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("col1,col2\na,b\n", encoding="utf-8")
    handler = ReviewSessionHandler()
    status, body = handler.post_load({"csv_path": str(bad_csv)})
    assert status == 422


def test_review_session_load_accepts_valid_csv_and_lists(tmp_path: Path) -> None:
    csv_path = _make_valid_csv(tmp_path)
    manager = SessionManager()
    handler = ReviewSessionHandler(session_manager=manager)
    status, body = handler.post_load({"csv_path": str(csv_path)})
    assert status == 200
    assert "session_id" in body

    list_status, list_body = handler.get_sessions()
    assert list_status == 200
    assert len(list_body["sessions"]) == 1


def test_review_action_confirm_candidate(tmp_path: Path) -> None:
    csv_path = _make_valid_csv(tmp_path)
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    _, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    session_id = load_body["session_id"]

    # Inject a candidate into session
    state = manager.get(session_id)
    assert state is not None
    updated = dict(state.payload or {})
    updated["candidates"] = [
        {"candidate_id": "cand_1", "extracted_name": "Alice", "status": "pending"}
    ]
    manager.upsert(session_id, state.csv_path, updated)

    actions_handler = ReviewActionsHandler(session_manager=manager)
    status, body = actions_handler.post_action(
        session_id, {"action_type": "confirm", "target_ids": ["cand_1"]}
    )
    assert status == 200
    assert body["persisted"] is True

    state = manager.get(session_id)
    assert state is not None
    cands = state.payload.get("candidates", [])
    assert cands[0]["status"] == "confirmed"


def test_review_action_undo(tmp_path: Path) -> None:
    csv_path = _make_valid_csv(tmp_path)
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    _, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    session_id = load_body["session_id"]

    state = manager.get(session_id)
    assert state is not None
    updated = dict(state.payload or {})
    candidate = {"candidate_id": "cand_2", "extracted_name": "Bob", "status": "pending"}
    updated["candidates"] = [candidate]
    updated["candidates_original"] = [candidate]
    manager.upsert(session_id, state.csv_path, updated)

    actions_handler = ReviewActionsHandler(session_manager=manager)
    actions_handler.post_action(session_id, {"action_type": "reject", "target_ids": ["cand_2"]})
    status, body = actions_handler.post_undo(session_id)
    assert status == 200
    assert body["remaining_undo_count"] == 0
