from __future__ import annotations

from time import perf_counter

from src.web.app.session_query_service import QueryFilters, SessionQueryService


def test_search_filter_performance_500_candidates_under_200ms() -> None:
    candidates = [
        {
            "candidate_id": f"c{i}",
            "extracted_name": "PlayerAlpha" if i % 3 == 0 else "PlayerBeta",
            "status": "pending",
        }
        for i in range(500)
    ]

    start = perf_counter()
    filtered = SessionQueryService.filter_candidates(candidates, QueryFilters(search_text="alpha"))
    elapsed_ms = (perf_counter() - start) * 1000

    assert len(filtered) > 0
    assert elapsed_ms <= 200
