from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any


@dataclass
class _LockState:
    video_id: str
    owner_session_id: str
    mode: str = "writer"


class ReviewLockService:
    """In-process single-writer lock model with read-only fallback for other sessions."""

    def __init__(self) -> None:
        self._guard = RLock()
        self._locks: dict[str, _LockState] = {}

    def acquire(self, video_id: str, session_id: str) -> dict[str, Any]:
        with self._guard:
            state = self._locks.get(video_id)
            if state is None:
                state = _LockState(video_id=video_id, owner_session_id=session_id)
                self._locks[video_id] = state
            is_owner = state.owner_session_id == session_id
            return {
                "video_id": video_id,
                "mode": state.mode,
                "owner_session_id": state.owner_session_id,
                "is_current_session_owner": is_owner,
                "readonly": not is_owner,
            }

    def get(self, video_id: str, session_id: str | None = None) -> dict[str, Any]:
        with self._guard:
            state = self._locks.get(video_id)
            if state is None:
                return {
                    "video_id": video_id,
                    "mode": "writer",
                    "owner_session_id": None,
                    "is_current_session_owner": True,
                    "readonly": False,
                }
            is_owner = session_id is not None and state.owner_session_id == session_id
            return {
                "video_id": video_id,
                "mode": state.mode,
                "owner_session_id": state.owner_session_id,
                "is_current_session_owner": bool(is_owner),
                "readonly": not bool(is_owner),
            }

    def ensure_writable(self, video_id: str, session_id: str) -> tuple[bool, dict[str, Any] | None]:
        state = self.get(video_id, session_id)
        if state["readonly"]:
            return False, {
                "error": "workspace_locked",
                "message": "Read-only: another editor is actively writing this video",
                "lock": {
                    "owner_session_id": state["owner_session_id"],
                },
            }
        return True, None

    def release(self, video_id: str, session_id: str) -> None:
        with self._guard:
            state = self._locks.get(video_id)
            if state and state.owner_session_id == session_id:
                self._locks.pop(video_id, None)
