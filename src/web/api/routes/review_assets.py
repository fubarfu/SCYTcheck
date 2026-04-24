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

    def get_thumbnail(self, session_id: str, candidate_id: str) -> tuple[int, dict]:
        state = self.sessions.get(session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"session_id {session_id} not found"}

        csv_path = Path(state.csv_path)
        persisted = self.frame_store.persisted_frame_path(csv_path, candidate_id)
        if persisted.exists():
            return 200, {
                "candidate_id": candidate_id,
                "thumbnail_url": f"/api/assets/frames/{candidate_id}.png",
            }

        cache_path = self.frame_store.cache_thumbnail_path(session_id, candidate_id)
        if cache_path.exists():
            return 200, {
                "candidate_id": candidate_id,
                "thumbnail_url": f"/api/assets/cache/{session_id}/{candidate_id}.png",
            }

        return 404, {
            "error": "not_found",
            "message": f"No thumbnail available for candidate {candidate_id}",
        }
