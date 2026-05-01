from __future__ import annotations

import json
import logging
import shutil
import time
from pathlib import Path
from typing import Any


LEGACY_WORKSPACE_DIRNAME = ".scyt_review_workspaces"


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

        if not any(root.exists() for root in self._workspace_roots(project_location)):
            self._cache[cache_key] = (now, [])
            return []

        discovered_by_id: dict[str, dict[str, Any]] = {}
        for root in self._workspace_roots(project_location):
            if not root.exists() or not root.is_dir():
                continue

            for child in root.iterdir():
                if not child.is_dir():
                    continue

                metadata_path = child / "metadata.json"
                if not metadata_path.exists():
                    continue

                metadata = self._load_metadata(metadata_path)
                if metadata is None:
                    continue

                project = {
                    "project_id": str(metadata.get("project_id") or child.name),
                    "video_url": str(metadata.get("video_url") or child.name),
                    "project_location": str(child),
                    "created_date": str(metadata.get("created_date") or ""),
                    "run_count": int(metadata.get("run_count") or 0),
                    "last_analyzed": str(metadata.get("last_analyzed") or metadata.get("created_date") or ""),
                    "candidate_count_total": int(metadata.get("candidate_count_total") or 0),
                    "candidate_count_reviewed": int(metadata.get("candidate_count_reviewed") or 0),
                }
                project_id = str(project.get("project_id") or "")
                existing = discovered_by_id.get(project_id)
                if existing is None or str(project.get("created_date") or "") >= str(existing.get("created_date") or ""):
                    discovered_by_id[project_id] = project

        results = sorted(discovered_by_id.values(), key=lambda item: item.get("created_date", ""), reverse=True)
        self._cache[cache_key] = (now, results)
        return list(results)

    @staticmethod
    def _workspace_roots(project_location: str) -> list[Path]:
        root = Path(project_location)
        roots = [root]
        legacy_root = root / LEGACY_WORKSPACE_DIRNAME
        if legacy_root not in roots:
            roots.append(legacy_root)
        return roots

    @classmethod
    def resolve_workspace_root(cls, project_location: str, project_id: str) -> Path | None:
        normalized_project_id = str(project_id).strip()
        if not normalized_project_id:
            return None

        for root in cls._workspace_roots(project_location):
            candidate = root / normalized_project_id
            if candidate.exists() and candidate.is_dir():
                return candidate
        return None

    def get_project_detail(self, project_location: str, project_id: str) -> dict[str, Any] | None:
        for project in self.discover_projects(project_location):
            if str(project.get("project_id")) == project_id:
                return project
        return None

    def delete_project(self, project_location: str, project_id: str) -> bool:
        project = self.get_project_detail(project_location, project_id)
        if project is None:
            return False

        project_path = Path(str(project.get("project_location") or "")).resolve()
        root_path = Path(project_location).resolve()

        try:
            project_path.relative_to(root_path)
        except ValueError:
            # Safety guard: only delete directories under the configured project root.
            return False

        if not project_path.exists() or not project_path.is_dir():
            return False

        shutil.rmtree(project_path)
        self.invalidate_cache(project_location)
        return True

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
