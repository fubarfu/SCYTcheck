from __future__ import annotations

from pathlib import Path
from typing import Any

from src.web.api.schemas import ReviewHistoryRestoreRequestDTO, SchemaValidationError
from src.web.app.review_history_store import ReviewHistoryStore
from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.web.app.session_manager import SessionManager, SessionState


class ReviewHistoryHandler:
    """Routes for workspace metadata, edit-history list/details, restore, and lock inspection."""

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        history_store: ReviewHistoryStore | None = None,
    ) -> None:
        self.sessions = session_manager or SessionManager()
        self.sidecar = ReviewSidecarStore()
        self.history_store = history_store or ReviewHistoryStore(self.sidecar)

    def _find_session_for_video(self, video_id: str, preferred_session_id: str | None = None) -> SessionState | None:
        if preferred_session_id:
            preferred = self.sessions.get(preferred_session_id)
            if preferred is not None:
                payload = self.sidecar.ensure_workspace_metadata(preferred.csv_path, dict(preferred.payload or {}))
                if str(payload.get("workspace", {}).get("video_id", "")) == video_id:
                    return preferred

        for state in self.sessions.list_sessions():
            payload = self.sidecar.ensure_workspace_metadata(state.csv_path, dict(state.payload or {}))
            if str(payload.get("workspace", {}).get("video_id", "")) == video_id:
                return state
        return None

    def get_workspace(self, video_id: str, session_id: str | None = None) -> tuple[int, dict[str, Any]]:
        state = self._find_session_for_video(video_id, preferred_session_id=session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"workspace {video_id} not found"}

        payload = self.sidecar.ensure_workspace_metadata(state.csv_path, dict(state.payload or {}))
        workspace = payload["workspace"]
        return 200, {
            "video_id": workspace["video_id"],
            "display_title": workspace["display_title"],
            "workspace_path": workspace["workspace_path"],
            "history_container_path": workspace["history_container_path"],
            "reviewed_names": sorted(
                {
                    str(name).strip()
                    for name in dict(payload.get("accepted_names", {})).values()
                    if str(name).strip()
                }
            ),
        }

    def get_history(self, video_id: str, session_id: str | None = None) -> tuple[int, dict[str, Any]]:
        state = self._find_session_for_video(video_id, preferred_session_id=session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"workspace {video_id} not found"}

        payload = self.sidecar.ensure_workspace_metadata(state.csv_path, dict(state.payload or {}))
        entries = self.history_store.list_entries(Path(state.csv_path), payload)
        dto_entries = [
            {
                "entry_id": entry["entry_id"],
                "created_at": entry["created_at"],
                "group_count": int(entry.get("summary", {}).get("group_count", 0)),
                "resolved_count": int(entry.get("summary", {}).get("resolved_count", 0)),
                "unresolved_count": int(entry.get("summary", {}).get("unresolved_count", 0)),
                "trigger_type": str(entry.get("trigger_type", "")),
                "compressed": bool(entry.get("compressed", False)),
            }
            for entry in entries
        ]
        return 200, {
            "video_id": video_id,
            "entries": dto_entries,
            "next_cursor": None,
        }

    def get_history_entry(
        self,
        video_id: str,
        entry_id: str,
        session_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        state = self._find_session_for_video(video_id, preferred_session_id=session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"workspace {video_id} not found"}

        payload = self.sidecar.ensure_workspace_metadata(state.csv_path, dict(state.payload or {}))
        entry = self.history_store.get_entry(Path(state.csv_path), payload, entry_id)
        if entry is None:
            return 404, {"error": "not_found", "message": f"history entry {entry_id} not found"}

        return 200, {
            "entry_id": entry["entry_id"],
            "created_at": entry["created_at"],
            "snapshot": dict(entry.get("snapshot", {})),
        }

    def post_restore(self, video_id: str, entry_id: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        try:
            dto = ReviewHistoryRestoreRequestDTO.from_payload(body)
        except SchemaValidationError as exc:
            return 400, {"error": "validation_error", "message": str(exc)}

        state = self._find_session_for_video(video_id, preferred_session_id=dto.session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"workspace {video_id} not found"}

        payload = self.sidecar.ensure_workspace_metadata(state.csv_path, dict(state.payload or {}))
        try:
            restored_payload, restore_entry_id = self.history_store.restore_snapshot(
                Path(state.csv_path),
                payload,
                entry_id,
                dto.create_restore_snapshot,
            )
        except FileNotFoundError as exc:
            return 404, {"error": "not_found", "message": str(exc)}

        self.sessions.upsert(state.session_id, state.csv_path, restored_payload)
        self.sessions.clear_history_pending(state.session_id)
        self.sidecar.save(Path(state.csv_path), restored_payload)
        return 200, {
            "video_id": video_id,
            "restored_entry_id": entry_id,
            "created_restore_entry_id": None,
            "status": "restored",
        }
