from __future__ import annotations

from src.web.api.routes.review_actions import _apply_action
from src.web.app.session_query_service import QueryFilters, SessionQueryService


def test_actions_on_visible_candidates_do_not_touch_hidden_candidates() -> None:
    candidates = [
        {"candidate_id": "c1", "extracted_name": "Alice", "status": "pending"},
        {"candidate_id": "c2", "extracted_name": "Alicia", "status": "pending"},
        {"candidate_id": "c3", "extracted_name": "Bob", "status": "pending"},
    ]

    visible = SessionQueryService.filter_candidates(candidates, QueryFilters(search_text="ali"))
    visible_ids = [c["candidate_id"] for c in visible]

    updated = _apply_action(candidates, "confirm", visible_ids, {})
    by_id = {c["candidate_id"]: c for c in updated}

    assert by_id["c1"]["status"] == "confirmed"
    assert by_id["c2"]["status"] == "confirmed"
    assert by_id["c3"]["status"] == "pending"
