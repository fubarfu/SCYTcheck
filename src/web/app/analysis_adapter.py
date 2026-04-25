from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from threading import Event, Lock, Thread
from typing import Any


class RunStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AnalysisRunState:
    run_id: str
    status: RunStatus = RunStatus.IDLE
    frames_processed: int = 0
    frames_estimated_total: int = 0
    stage_label: str = ""
    output_csv_path: str | None = None
    history_id: str | None = None
    history_run_id: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


ProgressCallback = Callable[[AnalysisRunState], None]  # noqa: E501


class AnalysisAdapter:
    """Async bridge between FastAPI handlers and synchronous AnalysisService."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._runs: dict[str, AnalysisRunState] = {}
        self._stop_events: dict[str, Event] = {}

    def start(
        self,
        run_id: str,
        target: Callable[[], Any],
        on_progress: ProgressCallback | None = None,
    ) -> AnalysisRunState:
        with self._lock:
            existing = self._runs.get(run_id)
            if existing and existing.status == RunStatus.RUNNING:
                raise ValueError(f"Run {run_id} is already running")

            stop_event = Event()
            state = AnalysisRunState(
                run_id=run_id,
                status=RunStatus.RUNNING,
                started_at=datetime.now(UTC),
            )
            self._runs[run_id] = state
            self._stop_events[run_id] = stop_event

        def worker() -> None:
            try:
                result = target()
                with self._lock:
                    state.output_csv_path = result if isinstance(result, str) else None
                    state.status = RunStatus.COMPLETED
                    state.ended_at = datetime.now(UTC)
            except Exception as exc:
                with self._lock:
                    state.status = RunStatus.FAILED
                    state.error_message = str(exc)
                    state.ended_at = datetime.now(UTC)
            finally:
                if on_progress is not None:
                    on_progress(state)

        Thread(target=worker, daemon=True, name=f"analysis-{run_id}").start()
        return state

    def progress(self, run_id: str) -> AnalysisRunState | None:
        with self._lock:
            return self._runs.get(run_id)

    def stop(self, run_id: str) -> AnalysisRunState | None:
        with self._lock:
            state = self._runs.get(run_id)
            stop_event = self._stop_events.get(run_id)
            if state and state.status == RunStatus.RUNNING:
                state.status = RunStatus.STOPPING
                if stop_event is not None:
                    stop_event.set()
        return state

    def get_stop_event(self, run_id: str) -> Event | None:
        with self._lock:
            return self._stop_events.get(run_id)

    def update_progress(
        self, run_id: str, frames_processed: int, total: int, label: str = ""
    ) -> None:
        with self._lock:
            state = self._runs.get(run_id)
            if state and state.status in {RunStatus.RUNNING, RunStatus.STOPPING}:
                state.frames_processed = frames_processed
                state.frames_estimated_total = total
                state.stage_label = label

    def set_history_metadata(self, run_id: str, history_id: str, history_run_id: str) -> None:
        with self._lock:
            state = self._runs.get(run_id)
            if state is None:
                return
            state.history_id = history_id
            state.history_run_id = history_run_id
