from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.session_manager import SessionManager


def _make_consensus_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "consensus.csv"
    csv_path.write_text(
        "#schema_version=1.0\n"
        "PlayerName,StartTimestamp\n"
        "Alice,00:00:01.000\n"
        "Alice,00:00:01.400\n",
        encoding="utf-8",
    )
    return csv_path


def _get_group(body: dict) -> dict:
    groups = body.get("groups", [])
    assert len(groups) == 1
    return groups[0]


def test_consensus_groups_default_collapsed_and_expand_reveals_occurrence_metadata(tmp_path: Path) -> None:
    manager = SessionManager()
    session_handler = ReviewSessionHandler(session_manager=manager)
    actions_handler = ReviewActionsHandler(session_manager=manager)

    csv_path = _make_consensus_csv(tmp_path)
    load_status, load_body = session_handler.post_load({"csv_path": str(csv_path)})
    assert load_status == 200
    session_id = load_body["session_id"]

    session_status, session_body = session_handler.get_session(session_id)
    assert session_status == 200

    group = _get_group(session_body)
    assert group["accepted_name"] == "Alice"
    assert group["accepted_name_summary"] == "Alice"
    assert group["resolution_status"] == "RESOLVED"
    assert group["is_collapsed"] is True
    assert group["active_spellings"] == ["Alice"]
    assert group["active_candidate_count"] == 2
    assert group["total_candidate_count"] == 2
    assert group["occurrence_count"] == 2

    toggle_status, _ = actions_handler.post_action(
        session_id,
        {
            "action_type": "toggle_collapse",
            "target_ids": [],
            "payload": {
                "group_id": group["group_id"],
                "is_collapsed": False,
            },
        },
    )
    assert toggle_status == 200

    expanded_status, expanded_body = session_handler.get_session(session_id)
    assert expanded_status == 200
    expanded_group = _get_group(expanded_body)
    assert expanded_group["is_collapsed"] is False
    assert len(expanded_group["candidates"]) == 2
    assert expanded_group["candidates"][0]["start_timestamp"]
