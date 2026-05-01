from __future__ import annotations

from pathlib import Path


class FrameAssetStore:
    """Resolves thumbnail and frame asset locations for review workflows."""

    def __init__(self, cache_root: Path) -> None:
        self.cache_root = cache_root
        self.cache_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def frame_folder_for_csv(csv_path: Path | str, workspace_path: Path | str | None = None) -> Path:
        if workspace_path is not None:
            return Path(workspace_path) / "frames"
        file_path = Path(csv_path)
        return file_path.parent / f"{file_path.stem}_frames"

    def persisted_frame_path(
        self,
        csv_path: Path | str,
        candidate_id: str,
        workspace_path: Path | str | None = None,
    ) -> Path:
        return self.frame_folder_for_csv(csv_path, workspace_path=workspace_path) / f"{candidate_id}.png"

    def cache_thumbnail_path(self, session_id: str, candidate_id: str) -> Path:
        session_dir = self.cache_root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir / f"{candidate_id}.png"
