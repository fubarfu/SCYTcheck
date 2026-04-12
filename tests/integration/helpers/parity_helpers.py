from __future__ import annotations


def assert_timestamp_parity(baseline: list[float], candidate: list[float]) -> None:
    assert len(baseline) == len(candidate)
    for left, right in zip(baseline, candidate, strict=True):
        assert abs(left - right) < 1e-9


def assert_frame_count_parity(baseline_count: int, candidate_count: int, tolerance: int = 1) -> None:
    assert abs(baseline_count - candidate_count) <= tolerance
