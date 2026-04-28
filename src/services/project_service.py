from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any


class ProjectService:
    """Filesystem project discovery for video-primary navigation."""

    def __init__(self, cache_ttl_seconds: float = 2.0) -> None:
        self._cache_ttl_seconds = max(0.0, cache_ttl_seconds)
        self._cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
        self._logger = logging.getLogger(__name__)

    def discover_projects(self, project_location: str) -> list[dict[str, Any]]:
        cache_key = str(Path(project_location).resolve())
        now = time.monotonic()
        cached = self._cache.get(cache_key)
        if cached and (now - cached[0]) <= self._cache_ttl_seconds:
            return list(cached[1])

        root = Path(project_location)
        if not root.exists():
            self._cache[cache_key] = (now, [])
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

        results = sorted(projects, key=lambda item: item.get("created_date", ""), reverse=True)
        self._cache[cache_key] = (now, results)
        return list(results)

    def get_project_detail(self, project_location: str, project_id: str) -> dict[str, Any] | None:
        for project in self.discover_projects(project_location):
            if str(project.get("project_id")) == project_id:
                return project
        return None

    def invalidate_cache(self, project_location: str | None = None) -> None:
        if project_location is None:
            self._cache.clear()
            return
        cache_key = str(Path(project_location).resolve())
        self._cache.pop(cache_key, None)

    def _load_metadata(self, metadata_path: Path) -> dict[str, Any] | None:
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._logger.warning("Skipping invalid project metadata at %s: %s", metadata_path, exc)
            return None
        if not isinstance(payload, dict):
            self._logger.warning("Skipping non-object project metadata at %s", metadata_path)
            return None
        return payload
