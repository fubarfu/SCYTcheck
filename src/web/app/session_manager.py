from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any


@dataclass
class SessionState:
    session_id: str
    csv_path: str
    payload: dict[str, Any] = field(default_factory=dict)
    has_pending_history: bool = False
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SessionManager:
    """In-memory registry for active review sessions."""

    def __init__(self, max_cached_sessions: int = 10) -> None:
        self._lock = RLock()
        self._sessions: dict[str, SessionState] = {}
        self._active_session_id: str | None = None
        self._max_cached_sessions = max_cached_sessions

    def upsert(self, session_id: str, csv_path: str, payload: dict[str, Any]) -> SessionState:
        with self._lock:
            existing = self._sessions.get(session_id)
            state = SessionState(
                session_id=session_id,
                csv_path=csv_path,
                payload=payload,
                has_pending_history=(existing.has_pending_history if existing is not None else False),
            )
            self._sessions[session_id] = state
            self._active_session_id = session_id
            if len(self._sessions) > self._max_cached_sessions:
                oldest = min(self._sessions.values(), key=lambda s: s.updated_at)
                self._sessions.pop(oldest.session_id, None)
            return state

    def get(self, session_id: str) -> SessionState | None:
        with self._lock:
            return self._sessions.get(session_id)

    def list_sessions(self) -> list[SessionState]:
        with self._lock:
            return sorted(self._sessions.values(), key=lambda item: item.updated_at, reverse=True)

    def remove(self, session_id: str) -> bool:
        with self._lock:
            removed = self._sessions.pop(session_id, None) is not None
            if removed and self._active_session_id == session_id:
                self._active_session_id = next(iter(self._sessions), None)
            return removed

    def switch_session(self, session_id: str) -> SessionState | None:
        with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                return None
            self._active_session_id = session_id
            return state

    def mark_history_pending(self, session_id: str) -> bool:
        with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                return False
            state.has_pending_history = True
            state.updated_at = datetime.now(UTC)
            return True

    def clear_history_pending(self, session_id: str) -> bool:
        with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                return False
            state.has_pending_history = False
            state.updated_at = datetime.now(UTC)
            return True

    def get_active_session(self) -> SessionState | None:
        with self._lock:
            if self._active_session_id is None:
                return None
            return self._sessions.get(self._active_session_id)
