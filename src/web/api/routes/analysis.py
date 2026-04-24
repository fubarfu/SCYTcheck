from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from src.web.api.schemas import AnalysisStartRequestDTO, SchemaValidationError
from src.web.app.analysis_adapter import AnalysisAdapter, RunStatus


class AnalysisHandler:
    """HTTP-style handler for analysis start/progress/stop/result endpoints."""

    def __init__(
        self,
        adapter: AnalysisAdapter | None = None,
    ) -> None:
        self.adapter = adapter or AnalysisAdapter()

    def post_start(self, payload: dict[str, Any]) -> tuple[int, dict]:
        try:
            dto = AnalysisStartRequestDTO.from_payload(payload)
        except SchemaValidationError as exc:
            return 400, {"error": "validation_error", "message": str(exc)}

        output_folder = Path(dto.output_folder)
        if not output_folder.exists():
            return 400, {"error": "validation_error", "message": "output_folder does not exist"}

        run_id = f"run_{uuid.uuid4().hex[:12]}"

        def work() -> str:
            output_path = output_folder / dto.output_filename
            output_path.write_text("PlayerName,StartTimestamp\n", encoding="utf-8")
            return str(output_path)

        try:
            self.adapter.start(run_id, work)
        except ValueError as exc:
            return 409, {"error": "conflict", "message": str(exc)}

        return 202, {"run_id": run_id, "status": RunStatus.RUNNING.value}

    def get_progress(self, run_id: str) -> tuple[int, dict]:
        state = self.adapter.progress(run_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"run_id {run_id} not found"}

        return 200, {
            "run_id": state.run_id,
            "status": state.status.value,
            "stage_label": state.stage_label,
            "frames_processed": state.frames_processed,
            "frames_estimated_total": state.frames_estimated_total,
        }

    def post_stop(self, run_id: str) -> tuple[int, dict]:
        state = self.adapter.stop(run_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"run_id {run_id} not found"}
        return 202, {"run_id": state.run_id, "status": state.status.value}

    def get_result(self, run_id: str) -> tuple[int, dict]:
        state = self.adapter.progress(run_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"run_id {run_id} not found"}
        if state.status not in {RunStatus.COMPLETED, RunStatus.FAILED}:
            return 202, {"run_id": run_id, "status": state.status.value}

        partial = state.status == RunStatus.FAILED
        return 200, {
            "run_id": run_id,
            "status": state.status.value,
            "csv_path": state.output_csv_path,
            "partial": partial,
        }
