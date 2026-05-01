from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.session_manager import SessionManager


def _make_conflict_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "conflict.csv"
    csv_path.write_text(
        "#schema_version=1.0\n"
        "PlayerName,StartTimestamp\n"
        "Alicia,00:00:01.000\n"
        "Alice,00:00:01.300\n",
        encoding="utf-8",
    )
    return csv_path


def _single_group(body: dict) -> dict:
    groups = body.get("groups", [])
    assert len(groups) == 1
    return groups[0]


def test_conflict_groups_default_open_and_manual_toggle_persists_on_reload(tmp_path: Path) -> None:
    csv_path = _make_conflict_csv(tmp_path)

    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    session_status, session_body = session_handler.get_session(session_id)
    assert session_status == 200
    group = _single_group(session_body)

    assert group["resolution_status"] == "UNRESOLVED"
    assert group["accepted_name"] is None
    assert group["active_spellings"] == ["Alice", "Alicia"]
    assert group["is_collapsed"] is False

    collapse_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "toggle_collapse",
            "target_ids": [],
            "payload": {
                "group_id": group["group_id"],
                "is_collapsed": True,
            },
        },
    )
    assert collapse_status == 200

    collapsed_status, collapsed_body = session_handler.get_session(session_id)
    assert collapsed_status == 200
    collapsed_group = _single_group(collapsed_body)
    assert collapsed_group["resolution_status"] == "UNRESOLVED"
    assert collapsed_group["is_collapsed"] is True

    # Reload from disk-backed sidecar and verify manual toggle hydration survives.
    reloaded_manager = SessionManager()
    reloaded_session_handler = ReviewSessionHandler(session_manager=reloaded_manager)
    reload_status, reload_body = reloaded_session_handler.post_load({"csv_path": str(csv_path)})
    assert reload_status == 200
    reload_session_id = reload_body["session_id"]

    hydrated_status, hydrated_body = reloaded_session_handler.get_session(reload_session_id)
    assert hydrated_status == 200
    hydrated_group = _single_group(hydrated_body)
    assert hydrated_group["resolution_status"] == "UNRESOLVED"
    assert hydrated_group["active_spellings"] == ["Alice", "Alicia"]
    assert hydrated_group["is_collapsed"] is True
