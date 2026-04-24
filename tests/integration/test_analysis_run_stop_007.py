from __future__ import annotations

import time
from pathlib import Path

from src.web.app.analysis_adapter import AnalysisAdapter, RunStatus


def test_analysis_adapter_starts_and_completes_run(tmp_path: Path) -> None:
    adapter = AnalysisAdapter()
    csv_path = str(tmp_path / "result.csv")

    def fake_work() -> str:
        return csv_path

    state = adapter.start("run_001", fake_work)
    assert state.run_id == "run_001"

    for _ in range(50):
        time.sleep(0.05)
        s = adapter.progress("run_001")
        if s and s.status == RunStatus.COMPLETED:
            break

    final = adapter.progress("run_001")
    assert final is not None
    assert final.status == RunStatus.COMPLETED
    assert final.output_csv_path == csv_path


def test_analysis_adapter_stop_signals_stopping(tmp_path: Path) -> None:
    adapter = AnalysisAdapter()
    barrier_started = __import__("threading").Event()
    barrier_held = __import__("threading").Event()

    def slow_work() -> str:
        barrier_started.set()
        barrier_held.wait(timeout=2.0)
        return "some.csv"

    adapter.start("run_002", slow_work)
    barrier_started.wait(timeout=2.0)

    result = adapter.stop("run_002")
    assert result is not None
    assert result.status == RunStatus.STOPPING
    barrier_held.set()
