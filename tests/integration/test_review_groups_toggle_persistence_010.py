from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.session_manager import SessionManager


def _make_toggle_persistence_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "toggle_persistence.csv"
    csv_path.write_text(
        "#schema_version=1.0\n"
        "PlayerName,StartTimestamp\n"
        "Alice,00:00:01.000\n"
        "Alice,00:00:01.300\n"
        "Alice,00:00:10.000\n"
        "Alicia,00:00:10.300\n",
        encoding="utf-8",
    )
    return csv_path


def test_mixed_group_toggle_state_persists_across_reload(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_toggle_persistence_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    session_status, session_body = session_handler.get_session(session_id)
    assert session_status == 200
    groups = session_body.get("groups", [])
    resolved_group = next(group for group in groups if group["resolution_status"] == "RESOLVED")
    unresolved_group = next(group for group in groups if group["resolution_status"] == "UNRESOLVED")

    expand_resolved_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "toggle_collapse",
            "target_ids": [],
            "payload": {
                "group_id": resolved_group["group_id"],
                "is_collapsed": False,
            },
        },
    )
    assert expand_resolved_status == 200

    collapse_unresolved_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "toggle_collapse",
            "target_ids": [],
            "payload": {
                "group_id": unresolved_group["group_id"],
                "is_collapsed": True,
            },
        },
    )
    assert collapse_unresolved_status == 200

    updated_status, updated_body = session_handler.get_session(session_id)
    assert updated_status == 200
    updated_groups = {group["group_id"]: group for group in updated_body["groups"]}
    assert updated_groups[resolved_group["group_id"]]["is_collapsed"] is False
    assert updated_groups[unresolved_group["group_id"]]["is_collapsed"] is True

    reloaded_manager = SessionManager()
    reloaded_session_handler = ReviewSessionHandler(session_manager=reloaded_manager)
    reload_status, reload_body = reloaded_session_handler.post_load({"csv_path": str(csv_path)})
    assert reload_status == 200
    reload_session_id = reload_body["session_id"]

    hydrated_status, hydrated_body = reloaded_session_handler.get_session(reload_session_id)
    assert hydrated_status == 200
    hydrated_groups = {group["group_id"]: group for group in hydrated_body["groups"]}
    assert hydrated_groups[resolved_group["group_id"]]["is_collapsed"] is False
    assert hydrated_groups[unresolved_group["group_id"]]["is_collapsed"] is True


def test_toggle_state_persists_after_mutation_and_reload(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_toggle_persistence_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    session_status, session_body = session_handler.get_session(session_id)
    assert session_status == 200
    groups = session_body.get("groups", [])
    resolved_group = next(group for group in groups if group["resolution_status"] == "RESOLVED")
    unresolved_group = next(group for group in groups if group["resolution_status"] == "UNRESOLVED")

    status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "toggle_collapse",
            "target_ids": [],
            "payload": {
                "group_id": resolved_group["group_id"],
                "is_collapsed": False,
            },
        },
    )
    assert status == 200

    status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "toggle_collapse",
            "target_ids": [],
            "payload": {
                "group_id": unresolved_group["group_id"],
                "is_collapsed": True,
            },
        },
    )
    assert status == 200

    reject_target = unresolved_group["candidates"][0]["candidate_id"]
    status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "reject",
            "target_ids": [reject_target],
            "payload": {"group_id": unresolved_group["group_id"]},
        },
    )
    assert status == 200

    updated_status, updated_body = session_handler.get_session(session_id)
    assert updated_status == 200
    updated_groups = {group["group_id"]: group for group in updated_body["groups"]}
    assert updated_groups[resolved_group["group_id"]]["is_collapsed"] is False
    assert updated_groups[unresolved_group["group_id"]]["is_collapsed"] is True

    reloaded_manager = SessionManager()
    reloaded_session_handler = ReviewSessionHandler(session_manager=reloaded_manager)
    reload_status, reload_body = reloaded_session_handler.post_load({"csv_path": str(csv_path)})
    assert reload_status == 200
    reload_session_id = reload_body["session_id"]

    hydrated_status, hydrated_body = reloaded_session_handler.get_session(reload_session_id)
    assert hydrated_status == 200
    hydrated_groups = {group["group_id"]: group for group in hydrated_body["groups"]}
    assert hydrated_groups[resolved_group["group_id"]]["is_collapsed"] is False
    assert hydrated_groups[unresolved_group["group_id"]]["is_collapsed"] is True
