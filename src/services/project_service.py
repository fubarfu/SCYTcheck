from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ProjectService:
    """Filesystem project discovery for video-primary navigation."""

    def discover_projects(self, project_location: str) -> list[dict[str, Any]]:
        root = Path(project_location)
        if not root.exists():
            return []

        projects: list[dict[str, Any]] = []
        for child in root.iterdir():
            if not child.is_dir():
                continue

            metadata_path = child / "metadata.json"
            if not metadata_path.exists():
                continue

            metadata = self._load_metadata(metadata_path)
            if metadata is None:
                continue

            projects.append(
                {
                    "project_id": str(metadata.get("project_id") or child.name),
                    "video_url": str(metadata.get("video_url") or child.name),
                    "project_location": str(child),
                    "created_date": str(metadata.get("created_date") or ""),
                    "run_count": int(metadata.get("run_count") or 0),
                    "last_analyzed": str(metadata.get("last_analyzed") or metadata.get("created_date") or ""),
                    "candidate_count_total": int(metadata.get("candidate_count_total") or 0),
                    "candidate_count_reviewed": int(metadata.get("candidate_count_reviewed") or 0),
                }
            )

        return sorted(projects, key=lambda item: item.get("created_date", ""), reverse=True)

    def get_project_detail(self, project_location: str, project_id: str) -> dict[str, Any] | None:
        for project in self.discover_projects(project_location):
            if str(project.get("project_id")) == project_id:
                return project
        return None

    @staticmethod
    def _load_metadata(metadata_path: Path) -> dict[str, Any] | None:
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        return payload
