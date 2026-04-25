from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.session_manager import SessionManager


def _make_contract_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "review_groups_contract.csv"
    csv_path.write_text(
        "#schema_version=1.0\n"
        "PlayerName,StartTimestamp\n"
        "Alice,00:00:01.000\n"
        "Alicia,00:00:01.200\n",
        encoding="utf-8",
    )
    return csv_path


def _load_session(tmp_path: Path) -> tuple[ReviewSessionHandler, ReviewActionsHandler, str, dict]:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_contract_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    get_status, body = session_handler.get_session(session_id)
    assert get_status == 200
    return session_handler, actions_handler, session_id, body


def _first_group(session_payload: dict) -> dict:
    groups = session_payload.get("groups", [])
    assert len(groups) == 1
    return groups[0]


def test_actions_contract_confirm_and_reject_flow(tmp_path: Path) -> None:
    session_handler, actions_handler, session_id, loaded = _load_session(tmp_path)
    group = _first_group(loaded)
    candidate_id = group["candidates"][0]["candidate_id"]

    confirm_status, confirm_body = actions_handler.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [candidate_id],
            "payload": {"group_id": group["group_id"]},
        },
    )

    assert confirm_status == 200
    assert confirm_body["persisted"] is True

    confirmed_status, confirmed_body = session_handler.get_session(session_id)
    assert confirmed_status == 200
    confirmed_group = _first_group(confirmed_body)
    assert confirmed_group["accepted_name"] == "Alice"
    assert confirmed_group["resolution_status"] == "RESOLVED"

    reject_status, reject_body = actions_handler.post_action(
        session_id,
        {
            "action_type": "reject",
            "target_ids": [candidate_id],
            "payload": {"group_id": group["group_id"]},
        },
    )

    assert reject_status == 200
    assert reject_body["persisted"] is True

    rejected_status, rejected_body = session_handler.get_session(session_id)
    assert rejected_status == 200
    rejected_group = _first_group(rejected_body)
    assert rejected_group["accepted_name"] == "Alicia"
    assert rejected_group["resolution_status"] == "RESOLVED"
    assert rejected_group["is_collapsed"] is True
    assert candidate_id in rejected_group["rejected_candidate_ids"]


def test_actions_contract_deselect_clears_accepted_name_and_expands_group(tmp_path: Path) -> None:
    session_handler, actions_handler, session_id, loaded = _load_session(tmp_path)
    group = _first_group(loaded)
    candidate_id = group["candidates"][0]["candidate_id"]

    confirm_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [candidate_id],
            "payload": {"group_id": group["group_id"]},
        },
    )
    assert confirm_status == 200

    deselect_status, deselect_body = actions_handler.post_action(
        session_id,
        {
            "action_type": "deselect",
            "target_ids": [],
            "payload": {"group_id": group["group_id"]},
        },
    )

    assert deselect_status == 200
    assert deselect_body["persisted"] is True

    current_status, current_body = session_handler.get_session(session_id)
    assert current_status == 200
    current_group = _first_group(current_body)
    assert current_group["accepted_name"] is None
    assert current_group["resolution_status"] == "UNRESOLVED"
    assert current_group["is_collapsed"] is False


def test_actions_contract_unreject_restores_candidate(tmp_path: Path) -> None:
    session_handler, actions_handler, session_id, loaded = _load_session(tmp_path)
    group = _first_group(loaded)
    candidate_id = group["candidates"][1]["candidate_id"]

    reject_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "reject",
            "target_ids": [candidate_id],
            "payload": {"group_id": group["group_id"]},
        },
    )
    assert reject_status == 200

    unreject_status, unreject_body = actions_handler.post_action(
        session_id,
        {
            "action_type": "unreject",
            "target_ids": [candidate_id],
            "payload": {"group_id": group["group_id"]},
        },
    )

    assert unreject_status == 200
    assert unreject_body["persisted"] is True

    current_status, current_body = session_handler.get_session(session_id)
    assert current_status == 200
    current_group = _first_group(current_body)
    assert candidate_id not in current_group["rejected_candidate_ids"]
