from __future__ import annotations

from src.web.app.session_query_service import QueryFilters, SessionQueryService


def test_live_search_filter_matches_substring_case_insensitive() -> None:
    candidates = [
        {"candidate_id": "c1", "extracted_name": "Alice", "status": "pending"},
        {"candidate_id": "c2", "extracted_name": "ALICIA", "status": "pending"},
        {"candidate_id": "c3", "extracted_name": "Bob", "status": "pending"},
    ]
    out = SessionQueryService.filter_candidates(candidates, QueryFilters(search_text="ali"))
    assert [c["candidate_id"] for c in out] == ["c1", "c2"]


def test_status_filter_restricts_results() -> None:
    candidates = [
        {"candidate_id": "c1", "extracted_name": "Alice", "status": "confirmed"},
        {"candidate_id": "c2", "extracted_name": "Alicia", "status": "rejected"},
        {"candidate_id": "c3", "extracted_name": "Bob", "status": "pending"},
    ]
    out = SessionQueryService.filter_candidates(candidates, QueryFilters(status="confirmed"))
    assert [c["candidate_id"] for c in out] == ["c1"]
