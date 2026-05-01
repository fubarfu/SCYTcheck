from __future__ import annotations

from time import perf_counter
from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_export import ReviewExportHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.session_manager import SessionManager


def _make_duplicate_validation_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "review_groups_validation.csv"
    csv_path.write_text(
        "#schema_version=1.0\n"
        "PlayerName,StartTimestamp\n"
        "Alice,00:00:01.000\n"
        "Alice,00:00:01.200\n"
        "Bob,00:00:10.000\n",
        encoding="utf-8",
    )
    return csv_path


def _make_all_rejected_recovery_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "review_groups_all_rejected.csv"
    csv_path.write_text(
        "#schema_version=1.0\n"
        "PlayerName,StartTimestamp\n"
        "Alice,00:00:01.000\n"
        "Alicia,00:00:01.300\n",
        encoding="utf-8",
    )
    return csv_path


def test_duplicate_name_validation_blocks_action_and_preserves_group_state(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_duplicate_validation_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    before_status, before_body = session_handler.get_session(session_id)
    assert before_status == 200
    groups = before_body.get("groups", [])

    resolved_group = next(
        group
        for group in groups
        if any(candidate["extracted_name"] == "Alice" for candidate in group["candidates"])
    )
    target_candidate = next(
        candidate
        for candidate in resolved_group["candidates"]
        if candidate["extracted_name"] == "Alice"
    )

    move_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "move_candidate",
            "target_ids": [target_candidate["candidate_id"]],
            "payload": {
                "candidate_id": target_candidate["candidate_id"],
                "source_group_id": resolved_group["group_id"],
                "create_new_group": True,
            },
        },
    )
    assert move_status == 200

    mid_status, mid_body = session_handler.get_session(session_id)
    assert mid_status == 200
    mid_groups = mid_body.get("groups", [])
    moved_target_group = next(
        group
        for group in mid_groups
        if any(candidate["candidate_id"] == target_candidate["candidate_id"] for candidate in group["candidates"])
    )
    source_group_after_move = next(group for group in mid_groups if group["group_id"] == resolved_group["group_id"])
    source_candidate_after_move = next(
        candidate
        for candidate in source_group_after_move["candidates"]
        if candidate["candidate_id"] != target_candidate["candidate_id"] and candidate["extracted_name"] == "Alice"
    )
    source_confirm_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [source_candidate_after_move["candidate_id"]],
            "payload": {"group_id": source_group_after_move["group_id"]},
        },
    )
    assert source_confirm_status == 200

    target_group_accepted_before = moved_target_group.get("accepted_name")
    target_group_resolution_before = moved_target_group.get("resolution_status")
    target_group_collapsed_before = moved_target_group.get("is_collapsed")
    target_candidate_status_before = next(
        candidate for candidate in moved_target_group["candidates"] if candidate["candidate_id"] == target_candidate["candidate_id"]
    ).get("status") or "pending"

    action_status, action_body = actions_handler.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [target_candidate["candidate_id"]],
            "payload": {"group_id": moved_target_group["group_id"]},
        },
    )

    assert action_status == 422
    assert action_body["error"] == "validation_error"
    assert action_body["validation"]["is_valid"] is False
    assert action_body["validation"]["conflict_group_id"] == resolved_group["group_id"]

    after_status, after_body = session_handler.get_session(session_id)
    assert after_status == 200

    after_target_group = next(
        group
        for group in after_body["groups"]
        if group["group_id"] == moved_target_group["group_id"]
    )
    assert after_target_group["accepted_name"] == target_group_accepted_before
    assert after_target_group["resolution_status"] == target_group_resolution_before
    assert after_target_group["is_collapsed"] == target_group_collapsed_before

    after_target_candidate = next(
        candidate
        for candidate in after_target_group["candidates"]
        if candidate["candidate_id"] == target_candidate["candidate_id"]
    )
    assert (after_target_candidate.get("status") or "pending") == target_candidate_status_before


def test_validation_feedback_latency_stays_under_500ms_for_duplicate_block(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_duplicate_validation_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    get_status, body = session_handler.get_session(session_id)
    assert get_status == 200
    groups = body.get("groups", [])
    resolved_group = next(
        group
        for group in groups
        if any(candidate["extracted_name"] == "Alice" for candidate in group["candidates"])
    )
    conflict_candidate = next(
        candidate
        for candidate in resolved_group["candidates"]
        if candidate["extracted_name"] == "Alice"
    )

    move_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "move_candidate",
            "target_ids": [conflict_candidate["candidate_id"]],
            "payload": {
                "candidate_id": conflict_candidate["candidate_id"],
                "source_group_id": resolved_group["group_id"],
                "create_new_group": True,
            },
        },
    )
    assert move_status == 200

    moved_status, moved_body = session_handler.get_session(session_id)
    assert moved_status == 200
    moved_groups = moved_body.get("groups", [])
    conflict_group = next(
        group
        for group in moved_groups
        if any(candidate["candidate_id"] == conflict_candidate["candidate_id"] for candidate in group["candidates"])
    )
    source_group_after_move = next(group for group in moved_groups if group["group_id"] == resolved_group["group_id"])
    source_candidate_after_move = next(
        candidate
        for candidate in source_group_after_move["candidates"]
        if candidate["candidate_id"] != conflict_candidate["candidate_id"] and candidate["extracted_name"] == "Alice"
    )
    source_confirm_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [source_candidate_after_move["candidate_id"]],
            "payload": {"group_id": source_group_after_move["group_id"]},
        },
    )
    assert source_confirm_status == 200

    started_at = perf_counter()
    status, response = actions_handler.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [conflict_candidate["candidate_id"]],
            "payload": {"group_id": conflict_group["group_id"]},
        },
    )
    elapsed_ms = (perf_counter() - started_at) * 1000

    assert status == 422
    assert response["error"] == "validation_error"
    assert elapsed_ms < 500


def test_move_candidate_recomputes_resolution_for_changed_existing_groups(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_duplicate_validation_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    get_status, body = session_handler.get_session(session_id)
    assert get_status == 200
    groups = body.get("groups", [])
    source_group = next(
        group
        for group in groups
        if any(candidate["extracted_name"] == "Alice" for candidate in group["candidates"])
    )
    target_group = next(group for group in groups if group["group_id"] != source_group["group_id"])

    moved_candidate = next(
        candidate
        for candidate in source_group["candidates"]
        if candidate["extracted_name"] == "Alice"
    )

    move_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "move_candidate",
            "target_ids": [moved_candidate["candidate_id"]],
            "payload": {
                "candidate_id": moved_candidate["candidate_id"],
                "source_group_id": source_group["group_id"],
                "to_group_id": target_group["group_id"],
            },
        },
    )
    assert move_status == 200

    after_status, after_body = session_handler.get_session(session_id)
    assert after_status == 200
    after_groups = {group["group_id"]: group for group in after_body.get("groups", [])}
    assert after_groups[source_group["group_id"]]["resolution_status"] == "UNRESOLVED"
    assert after_groups[target_group["group_id"]]["resolution_status"] == "UNRESOLVED"


def test_merge_groups_recomputes_target_group_resolution_status(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_duplicate_validation_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    get_status, body = session_handler.get_session(session_id)
    assert get_status == 200
    groups = body.get("groups", [])
    source_group = next(group for group in groups if group.get("accepted_name") != "Alice")
    target_group = next(group for group in groups if group["group_id"] != source_group["group_id"])

    merge_status, _ = actions_handler.post_action(
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
    assert merge_status == 200

    merged_status, merged_body = session_handler.get_session(session_id)
    assert merged_status == 200
    merged_groups = merged_body.get("groups", [])
    assert len(merged_groups) == 1
    assert merged_groups[0]["group_id"] == target_group["group_id"]
    assert merged_groups[0]["resolution_status"] == "UNRESOLVED"


def test_export_gate_blocks_unresolved_and_all_rejected_groups_until_recovered(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)
    export_handler = ReviewExportHandler(session_manager=manager)

    csv_path = _make_all_rejected_recovery_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    get_status, body = session_handler.get_session(session_id)
    assert get_status == 200
    groups = body.get("groups", [])
    conflict_group = next(group for group in groups if len(group.get("candidates", [])) >= 2)
    conflict_group_id = conflict_group["group_id"]
    cands = conflict_group["candidates"]
    assert len(cands) == 2

    for candidate in cands:
        reject_status, _ = actions_handler.post_action(
            session_id,
            {
                "action_type": "reject",
                "target_ids": [candidate["candidate_id"]],
                "payload": {"group_id": conflict_group_id},
            },
        )
        assert reject_status == 200

    blocked_status, blocked_body = export_handler.post_export(session_id)
    assert blocked_status == 422
    assert blocked_body["error"] == "completion_gate_failed"
    assert conflict_group_id in blocked_body["details"]["unresolved_group_ids"]

    recover_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "unreject",
            "target_ids": [cands[0]["candidate_id"]],
            "payload": {"group_id": conflict_group_id},
        },
    )
    assert recover_status == 200

    confirm_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [cands[0]["candidate_id"]],
            "payload": {"group_id": conflict_group_id},
        },
    )
    assert confirm_status == 200

    success_status, success_body = export_handler.post_export(session_id)
    assert success_status == 200
    assert success_body["deduplicated_count"] >= 1
