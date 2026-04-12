from __future__ import annotations

import time
from collections.abc import Callable


class Stopwatch:
    def __init__(self) -> None:
        self._started_at: float | None = None

    def start(self) -> None:
        self._started_at = time.perf_counter()

    def elapsed(self) -> float:
        if self._started_at is None:
            return 0.0
        return time.perf_counter() - self._started_at


def benchmark_callable(fn: Callable[[], object], repeat: int = 1) -> float:
    best = float("inf")
    for _ in range(max(1, repeat)):
        started = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - started)
    return best
