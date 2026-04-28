from __future__ import annotations

import json
from pathlib import Path

from src.services.project_service import ProjectService
from src.web.api.routes.projects import ProjectsHandler
from src.web.api.routes.settings import SettingsHandler
from src.web.app.settings_store import SettingsStore


def _settings_handler(tmp_path: Path, project_location: Path) -> SettingsHandler:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"project_location": str(project_location)}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return SettingsHandler(store=SettingsStore(settings_path=settings_path))


def test_projects_endpoint_discovers_filesystem_projects(tmp_path: Path) -> None:
    projects_root = tmp_path / "projects"
    projects_root.mkdir(parents=True)

    project_dir = projects_root / "video-abc"
    project_dir.mkdir()
    (project_dir / "metadata.json").write_text(
        json.dumps(
            {
                "project_id": "video-abc",
                "video_url": "https://www.youtube.com/watch?v=abc",
                "created_date": "2026-04-28T10:00:00Z",
                "run_count": 3,
                "last_analyzed": "2026-04-28T11:00:00Z",
                "candidate_count_total": 18,
                "candidate_count_reviewed": 9,
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    handler = ProjectsHandler(
        project_service=ProjectService(),
        settings_handler=_settings_handler(tmp_path, projects_root),
    )

    status, body = handler.get_projects()
    assert status == 200
    assert body["location_status"] == "valid"
    assert len(body["projects"]) == 1
    assert body["projects"][0]["project_id"] == "video-abc"


def test_projects_endpoint_handles_empty_location(tmp_path: Path) -> None:
    projects_root = tmp_path / "projects"
    projects_root.mkdir(parents=True)

    handler = ProjectsHandler(
        project_service=ProjectService(),
        settings_handler=_settings_handler(tmp_path, projects_root),
    )

    status, body = handler.get_projects()
    assert status == 200
    assert body["projects"] == []


def test_videos_refresh_after_settings_change(tmp_path: Path) -> None:
    old_root = tmp_path / "old-projects"
    old_root.mkdir(parents=True)

    new_root = tmp_path / "new-projects"
    new_root.mkdir(parents=True)

    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"project_location": str(old_root)}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    settings_handler = SettingsHandler(store=SettingsStore(settings_path=settings_path))
    projects_handler = ProjectsHandler(project_service=ProjectService(), settings_handler=settings_handler)

    status_before, body_before = projects_handler.get_projects()
    assert status_before == 200
    assert body_before["projects"] == []

    # Switch location (equivalent to settings save), then verify discovery refreshes.
    update_status, _ = settings_handler.put_settings({"project_location": str(new_root)})
    assert update_status == 200

    project_dir = new_root / "video-new"
    project_dir.mkdir()
    (project_dir / "metadata.json").write_text(
        json.dumps(
            {
                "project_id": "video-new",
                "video_url": "https://www.youtube.com/watch?v=new",
                "created_date": "2026-04-28T12:00:00Z",
                "run_count": 1,
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    status_after, body_after = projects_handler.get_projects()
    assert status_after == 200
    assert len(body_after["projects"]) == 1
    assert body_after["projects"][0]["project_id"] == "video-new"
