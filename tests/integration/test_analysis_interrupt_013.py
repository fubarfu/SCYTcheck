from __future__ import annotations

import time

from src.web.api.routes.analysis import AnalysisHandler
from src.web.app.analysis_adapter import AnalysisAdapter


def test_failed_analysis_exposes_recovery_payload() -> None:
    adapter = AnalysisAdapter()
    handler = AnalysisHandler(adapter=adapter)

    def failing_work() -> str:
        raise RuntimeError("analysis interrupted")

    adapter.start("run-interrupt-013", failing_work)

    for _ in range(50):
        status, progress = handler.get_progress("run-interrupt-013")
        assert status == 200
        if progress["status"] == "failed":
            break
        time.sleep(0.02)

    status, progress = handler.get_progress("run-interrupt-013")
    assert status == 200
    assert progress["status"] == "failed"
    assert progress["recovery_action"] == "retry_analysis"
    assert "interrupted" in str(progress.get("message", "")).lower()

    result_status, result_payload = handler.get_result("run-interrupt-013")
    assert result_status == 200
    assert result_payload["status"] == "failed"
    assert result_payload["partial"] is True
