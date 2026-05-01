from __future__ import annotations

import json
import logging
from pathlib import Path

from src.services.project_service import ProjectService


def _write_metadata(project_dir: Path, project_id: str = "video-1") -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "metadata.json").write_text(
        json.dumps(
            {
                "project_id": project_id,
                "video_url": f"https://example.test/{project_id}",
                "created_date": "2026-04-28T12:00:00Z",
                "run_count": 1,
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_discover_projects_uses_cache_until_invalidated(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    project_dir = root / "video-1"
    _write_metadata(project_dir)

    service = ProjectService(cache_ttl_seconds=60.0)

    first = service.discover_projects(str(root))
    assert len(first) == 1
    assert first[0]["project_id"] == "video-1"

    # Remove metadata after first scan; cache should preserve prior result.
    (project_dir / "metadata.json").unlink()
    cached = service.discover_projects(str(root))
    assert len(cached) == 1

    service.invalidate_cache(str(root))
    refreshed = service.discover_projects(str(root))
    assert refreshed == []


def test_discover_projects_logs_corrupt_metadata(tmp_path: Path, caplog) -> None:
    root = tmp_path / "projects"
    project_dir = root / "broken"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "metadata.json").write_text("{not-json", encoding="utf-8")

    service = ProjectService(cache_ttl_seconds=0.0)

    with caplog.at_level(logging.WARNING, logger="src.services.project_service"):
        result = service.discover_projects(str(root))

    assert result == []
    assert "Skipping invalid project metadata" in caplog.text
