from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_export import ReviewExportHandler
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


def _make_duplicate_contract_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "review_groups_duplicate_contract.csv"
    csv_path.write_text(
        "#schema_version=1.0\n"
        "PlayerName,StartTimestamp\n"
        "Alice,00:00:01.000\n"
        "Alice,00:00:01.200\n"
        "Alyce,00:00:10.000\n"
        "Alice,00:00:10.300\n",
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


def test_actions_contract_duplicate_name_validation_returns_conflict_group_reference(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_duplicate_contract_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    threshold_status, _ = session_handler.patch_thresholds(
        session_id,
        {
            "similarity_threshold": 50,
            "recommendation_threshold": 70,
        },
    )
    assert threshold_status == 200

    get_status, body = session_handler.get_session(session_id)
    assert get_status == 200
    groups = body.get("groups", [])
    assert len(groups) == 2

    resolved_group = next(group for group in groups if group["accepted_name"] == "Alice")
    conflict_group = next(group for group in groups if group["group_id"] != resolved_group["group_id"])
    conflict_candidate = next(
        candidate
        for candidate in conflict_group["candidates"]
        if candidate["extracted_name"] == "Alice"
    )

    status, response = actions_handler.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [conflict_candidate["candidate_id"]],
            "payload": {"group_id": conflict_group["group_id"]},
        },
    )

    assert status == 422
    assert response["error"] == "validation_error"
    assert response["validation"]["is_valid"] is False
    assert response["validation"]["candidate_name"] == "Alice"
    assert response["validation"]["conflict_group_id"] == resolved_group["group_id"]
    assert "already used" in response["validation"]["message"]


def test_export_contract_blocks_when_any_group_is_unresolved(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)
    export_handler = ReviewExportHandler(session_manager=manager)

    csv_path = _make_contract_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200

    session_id = load_body["session_id"]
    get_status, get_body = session_handler.get_session(session_id)
    assert get_status == 200
    first_group = get_body["groups"][0]

    deselect_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "deselect",
            "target_ids": [],
            "payload": {"group_id": first_group["group_id"]},
        },
    )
    assert deselect_status == 200

    export_status, export_body = export_handler.post_export(session_id)

    assert export_status == 422
    assert export_body["error"] == "completion_gate_failed"
    assert isinstance(export_body["details"]["unresolved_group_ids"], list)
    assert export_body["details"]["unresolved_group_ids"]
    assert export_body["details"]["duplicate_name_conflicts"] == []


def test_export_contract_blocks_when_accepted_names_are_duplicated(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    export_handler = ReviewExportHandler(session_manager=manager)

    csv_path = _make_duplicate_contract_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    threshold_status, _ = session_handler.patch_thresholds(
        session_id,
        {
            "similarity_threshold": 50,
            "recommendation_threshold": 70,
        },
    )
    assert threshold_status == 200

    state = manager.get(session_id)
    assert state is not None
    payload = dict(state.payload)
    groups = payload.get("groups", [])
    assert len(groups) == 2
    first_group_id = groups[0]["group_id"]
    second_group_id = groups[1]["group_id"]
    payload["accepted_names"] = {
      first_group_id: "Alice",
      second_group_id: "Alice",
    }
    manager.upsert(session_id, state.csv_path, payload)

    export_status, export_body = export_handler.post_export(session_id)

    assert export_status == 422
    assert export_body["error"] == "completion_gate_failed"
    assert export_body["details"]["unresolved_group_ids"] == []
    assert export_body["details"]["duplicate_name_conflicts"] == [
        {
            "name": "Alice",
            "group_ids": sorted([first_group_id, second_group_id]),
        }
    ]


def test_actions_contract_merge_groups_combines_source_into_target(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_duplicate_contract_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    threshold_status, _ = session_handler.patch_thresholds(
        session_id,
        {
            "similarity_threshold": 50,
            "recommendation_threshold": 70,
        },
    )
    assert threshold_status == 200

    before_status, before_body = session_handler.get_session(session_id)
    assert before_status == 200
    groups = before_body.get("groups", [])
    assert len(groups) == 2
    source_group = groups[1]
    target_group = groups[0]

    action_status, action_body = actions_handler.post_action(
        session_id,
        {
            "action_type": "merge_groups",
            "target_ids": [source_group["group_id"]],
            "payload": {
                "source_group_id": source_group["group_id"],
                "target_group_id": target_group["group_id"],
            },
        },
    )

    assert action_status == 200
    assert action_body["persisted"] is True

    merged_status, merged_body = session_handler.get_session(session_id)
    assert merged_status == 200
    merged_groups = merged_body.get("groups", [])
    assert len(merged_groups) == 1
    assert len(merged_groups[0]["candidates"]) == 4


def test_actions_contract_move_candidate_to_new_group_creates_new_group(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_duplicate_contract_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    threshold_status, _ = session_handler.patch_thresholds(
        session_id,
        {
            "similarity_threshold": 50,
            "recommendation_threshold": 70,
        },
    )
    assert threshold_status == 200

    before_status, before_body = session_handler.get_session(session_id)
    assert before_status == 200
    groups = before_body.get("groups", [])
    assert len(groups) == 2
    source_group = groups[0]
    candidate_id = source_group["candidates"][0]["candidate_id"]

    move_status, move_body = actions_handler.post_action(
        session_id,
        {
            "action_type": "move_candidate",
            "target_ids": [candidate_id],
            "payload": {
                "candidate_id": candidate_id,
                "source_group_id": source_group["group_id"],
                "create_new_group": True,
            },
        },
    )

    assert move_status == 200
    assert move_body["persisted"] is True

    moved_status, moved_body = session_handler.get_session(session_id)
    assert moved_status == 200
    moved_groups = moved_body.get("groups", [])
    assert len(moved_groups) == 3
    assert any(
        any(candidate["candidate_id"] == candidate_id for candidate in group.get("candidates", []))
        and group["group_id"].startswith("grp_manual_")
        for group in moved_groups
    )
