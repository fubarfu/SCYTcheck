from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_export import ReviewExportHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.session_manager import SessionManager


def _setup_session_with_candidates(tmp_path: Path) -> tuple[str, SessionManager]:
    csv_path = tmp_path / "result.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,5.0\nAlice,10.0\nBob,15.0\n",
        encoding="utf-8",
    )
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    _, body = session_handler.post_load({"csv_path": str(csv_path)})
    session_id = body["session_id"]

    state = manager.get(session_id)
    assert state is not None
    payload = dict(state.payload or {})
    payload["candidates"] = [
        {
            "candidate_id": "c001",
            "extracted_name": "Alice",
            "start_timestamp": "5.0",
            "status": "confirmed",
        },
        {
            "candidate_id": "c002",
            "extracted_name": "Alice",
            "start_timestamp": "10.0",
            "status": "confirmed",
        },
        {
            "candidate_id": "c003",
            "extracted_name": "Bob",
            "start_timestamp": "15.0",
            "status": "confirmed",
        },
    ]
    manager.upsert(session_id, state.csv_path, payload)
    return session_id, manager


def test_export_produces_deduplicated_names_csv(tmp_path: Path) -> None:
    session_id, manager = _setup_session_with_candidates(tmp_path)
    export_handler = ReviewExportHandler(session_manager=manager)
    status, body = export_handler.post_export(session_id)
    assert status == 200
    assert body["confirmed_count"] == 3
    assert body["deduplicated_count"] == 2

    names_csv = Path(body["deduplicated_names_csv_path"])
    assert names_csv.exists()
    content = names_csv.read_text(encoding="utf-8")
    assert "Alice" in content
    assert "Bob" in content


def test_export_produces_occurrences_csv(tmp_path: Path) -> None:
    session_id, manager = _setup_session_with_candidates(tmp_path)
    export_handler = ReviewExportHandler(session_manager=manager)
    _, body = export_handler.post_export(session_id)

    occ_csv = Path(body["occurrences_csv_path"])
    assert occ_csv.exists()
    rows = occ_csv.read_text(encoding="utf-8").splitlines()
    # Header + 3 rows
    assert len(rows) == 4


def test_export_excludes_rejected_candidates(tmp_path: Path) -> None:
    session_id, manager = _setup_session_with_candidates(tmp_path)
    # Reject one
    actions = ReviewActionsHandler(session_manager=manager)
    actions.post_action(session_id, {"action_type": "reject", "target_ids": ["c003"]})

    export_handler = ReviewExportHandler(session_manager=manager)
    _, body = export_handler.post_export(session_id)
    assert body["confirmed_count"] == 2
    assert body["deduplicated_count"] == 1
