from __future__ import annotations

from src.web.api.routes.review_actions import _apply_action


def test_bulk_confirm_and_reject() -> None:
    candidates = [
        {"candidate_id": "c1", "status": "pending"},
        {"candidate_id": "c2", "status": "pending"},
        {"candidate_id": "c3", "status": "pending"},
    ]
    updated = _apply_action(candidates, "confirm", ["c1", "c2"], {})
    updated = _apply_action(updated, "reject", ["c3"], {})
    by_id = {c["candidate_id"]: c["status"] for c in updated}
    assert by_id == {"c1": "confirmed", "c2": "confirmed", "c3": "rejected"}


def test_selective_candidate_confirmation() -> None:
    candidates = [
        {"candidate_id": "c1", "status": "pending"},
        {"candidate_id": "c2", "status": "pending"},
    ]
    updated = _apply_action(candidates, "confirm", ["c2"], {})
    by_id = {c["candidate_id"]: c["status"] for c in updated}
    assert by_id == {"c1": "pending", "c2": "confirmed"}
