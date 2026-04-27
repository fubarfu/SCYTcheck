from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

Handler = Callable[..., Any]


@dataclass(frozen=True)
class RouteRegistration:
    method: str
    path: str
    handler: Handler


class RouteRegistry:
    def __init__(self) -> None:
        self._routes: list[RouteRegistration] = []

    def add(self, method: str, path: str, handler: Handler) -> None:
        self._routes.append(RouteRegistration(method=method.upper(), path=path, handler=handler))

    def all(self) -> list[RouteRegistration]:
        return list(self._routes)


def map_error(exc: Exception) -> tuple[int, dict[str, str]]:
    if isinstance(exc, FileNotFoundError):
        return 404, {"error": "not_found", "message": str(exc)}
    if isinstance(exc, ValueError):
        return 400, {"error": "validation_error", "message": str(exc)}
    return 500, {"error": "internal_error", "message": "Unexpected server error"}


def build_router() -> RouteRegistry:
    """Register base routes that are always available in the local runtime."""
    router = RouteRegistry()
    router.add("GET", "/api/health", lambda: {"status": "ok"})

    # Review workflow endpoints (implemented by local web server handlers).
    router.add("GET", "/api/review/sessions", lambda: {})
    router.add("POST", "/api/review/sessions/load", lambda payload=None: payload)
    router.add("GET", "/api/review/sessions/{session_id}", lambda session_id: session_id)
    router.add("POST", "/api/review/sessions/{session_id}/actions", lambda session_id, payload=None: payload)
    router.add("POST", "/api/review/sessions/{session_id}/undo", lambda session_id: session_id)
    router.add("POST", "/api/review/sessions/{session_id}/recalculate", lambda session_id: session_id)

    router.add("GET", "/api/review/workspaces/{video_id}", lambda video_id: video_id)
    router.add("GET", "/api/review/workspaces/{video_id}/history", lambda video_id: video_id)
    router.add("GET", "/api/review/workspaces/{video_id}/history/{entry_id}", lambda video_id, entry_id: entry_id)
    router.add("POST", "/api/review/workspaces/{video_id}/history/{entry_id}/restore", lambda video_id, entry_id, payload=None: payload)
    router.add("GET", "/api/review/workspaces/{video_id}/lock", lambda video_id: video_id)

    router.add("GET", "/api/history/videos", lambda: {})
    router.add("GET", "/api/history/videos/{history_id}", lambda history_id: history_id)
    router.add("POST", "/api/history/merge-run", lambda payload=None: payload)
    router.add("POST", "/api/history/reopen", lambda payload=None: payload)
    router.add("DELETE", "/api/history/videos/{history_id}", lambda history_id: history_id)
    return router
