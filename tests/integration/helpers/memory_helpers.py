from __future__ import annotations


def checkpoint_indices(total_items: int) -> tuple[int, int, int]:
    if total_items <= 0:
        return 0, 0, 0
    return 0, total_items // 2, total_items - 1


def percent_delta(reference: float, current: float) -> float:
    if reference == 0:
        return 0.0
    return ((current - reference) / reference) * 100.0
