from __future__ import annotations

from pathlib import Path

from src.web.app.frame_asset_store import FrameAssetStore
from src.web.app.session_manager import SessionManager


class ReviewAssetsHandler:
    def __init__(
        self, session_manager: SessionManager | None = None, cache_root: Path | None = None
    ) -> None:
        self.sessions = session_manager or SessionManager()
        _cache_root = cache_root or Path.home() / ".scytcheck_cache" / "thumbs"
        self.frame_store = FrameAssetStore(cache_root=_cache_root)

    def get_thumbnail(
        self, session_id: str, candidate_id: str, *, project_location: str | None = None
    ) -> tuple[int, dict]:
        state = self.sessions.get(session_id)
        if state is None:
            # Fallback for video-context sessions not tracked by SessionManager
            if project_location:
                path = self._find_frame_in_project(project_location, candidate_id)
                if path is not None:
                    from urllib.parse import urlencode
                    qs = urlencode({"pl": project_location})
                    return 200, {
                        "candidate_id": candidate_id,
                        "thumbnail_url": f"/api/assets/video/{session_id}/{candidate_id}.png?{qs}",
                    }
            return 404, {"error": "not_found", "message": f"session_id {session_id} not found"}

        csv_path = Path(state.csv_path)
        workspace_path = dict(state.payload or {}).get("workspace", {}).get("workspace_path")
        persisted = self.frame_store.persisted_frame_path(csv_path, candidate_id, workspace_path=workspace_path)
        if persisted.exists():
            return 200, {
                "candidate_id": candidate_id,
                "thumbnail_url": f"/api/assets/frames/{session_id}/{candidate_id}.png",
            }

        cache_path = self.frame_store.cache_thumbnail_path(session_id, candidate_id)
        if cache_path.exists():
            return 200, {
                "candidate_id": candidate_id,
                "thumbnail_url": f"/api/assets/cache/{session_id}/{candidate_id}.png",
            }

        # Fallback: search legacy frame folders in the project location
        fallback_pl = project_location or workspace_path
        if fallback_pl:
            path = self._find_frame_in_project(str(fallback_pl), candidate_id)
            if path is not None:
                from urllib.parse import urlencode
                qs = urlencode({"pl": str(fallback_pl)})
                return 200, {
                    "candidate_id": candidate_id,
                    "thumbnail_url": f"/api/assets/video/{session_id}/{candidate_id}.png?{qs}",
                }

        return 404, {
            "error": "not_found",
            "message": f"No thumbnail available for candidate {candidate_id}",
        }

    def resolve_thumbnail_path(
        self,
        session_id: str,
        candidate_id: str,
        *,
        asset_kind: str | None = None,
        project_location: str | None = None,
    ) -> Path | None:
        state = self.sessions.get(session_id)
        if state is None:
            # Fallback for video-context sessions
            if project_location and asset_kind in (None, "video"):
                return self._find_frame_in_project(project_location, candidate_id)
            return None

        csv_path = Path(state.csv_path)
        workspace_path = dict(state.payload or {}).get("workspace", {}).get("workspace_path")
        persisted = self.frame_store.persisted_frame_path(csv_path, candidate_id, workspace_path=workspace_path)
        cache_path = self.frame_store.cache_thumbnail_path(session_id, candidate_id)

        if asset_kind == "frames":
            if persisted.exists():
                return persisted
            # Fallback: legacy frame folder layout when session is found but frames moved/missing
            fallback_pl = project_location or workspace_path
            if fallback_pl:
                return self._find_frame_in_project(str(fallback_pl), candidate_id)
            return None
        if asset_kind == "cache":
            return cache_path if cache_path.exists() else None

        if persisted.exists():
            return persisted
        if cache_path.exists():
            return cache_path
        # Fallback: legacy frame folder layout
        fallback_pl = project_location or workspace_path
        if fallback_pl:
            return self._find_frame_in_project(str(fallback_pl), candidate_id)
        return None

    @staticmethod
    def _find_frame_in_project(project_location: str, candidate_id: str) -> Path | None:
        """Find a candidate frame in workspace-style or CSV-style frame folders."""
        root = Path(project_location)
        if not root.exists():
            return None

        direct_frames = root / "frames" / f"{candidate_id}.png"
        if direct_frames.exists():
            return direct_frames

        for frames_dir in root.glob("*_frames"):
            candidate_path = frames_dir / f"{candidate_id}.png"
            if candidate_path.exists():
                return candidate_path
        return None
