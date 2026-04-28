from __future__ import annotations

from time import perf_counter

from src.services.review_service import ReviewService


def _build_run(start: int, count: int) -> dict[str, object]:
    return {
        "candidates": [
            {
                "candidate_id": f"cand_{idx}",
                "extracted_name": f"Player {idx}",
            }
            for idx in range(start, start + count)
        ]
    }


def test_merge_algorithm_handles_10k_candidates_under_500ms() -> None:
    """T092: profile merge+freshness path with 10k+ candidates."""
    service = ReviewService()

    # 15k candidate records across runs, with overlap to exercise deduplication.
    runs = [
        _build_run(0, 5000),
        _build_run(2500, 5000),
        _build_run(5000, 5000),
    ]

    started = perf_counter()
    merged = service._merge_candidates(runs, prior_decisions={})
    marked = service.mark_new_candidates(merged, runs, prior_decisions={})
    elapsed_ms = (perf_counter() - started) * 1000

    assert len(marked) == 10000
    assert elapsed_ms < 500, f"merge took {elapsed_ms:.2f}ms for 15k inputs"
