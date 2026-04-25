from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.session_manager import SessionManager


def _make_duplicate_validation_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "review_groups_validation.csv"
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


def test_duplicate_name_validation_blocks_action_and_preserves_group_state(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_duplicate_validation_csv(tmp_path)
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

    resolved_group = next(group for group in groups if group["accepted_name"] == "Alice")
    target_group = next(group for group in groups if group["group_id"] != resolved_group["group_id"])
    target_group_accepted_before = target_group.get("accepted_name")
    target_group_resolution_before = target_group.get("resolution_status")
    target_group_collapsed_before = target_group.get("is_collapsed")
    target_candidate = next(
        candidate
        for candidate in target_group["candidates"]
        if candidate["extracted_name"] == "Alice"
    )
    target_candidate_status_before = target_candidate.get("status") or "pending"

    action_status, action_body = actions_handler.post_action(
        session_id,
        {
            "action_type": "confirm",
            "target_ids": [target_candidate["candidate_id"]],
            "payload": {"group_id": target_group["group_id"]},
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
        if group["group_id"] == target_group["group_id"]
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
