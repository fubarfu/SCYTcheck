from __future__ import annotations

import json
from pathlib import Path

from src.services.project_service import ProjectService
from src.web.api.routes.projects import ProjectsHandler
from src.web.api.routes.settings import SettingsHandler
from src.web.app.settings_store import SettingsStore


def _make_settings_handler(tmp_path: Path, project_location: Path) -> SettingsHandler:
    settings_path = tmp_path / "scytcheck_settings.json"
    settings_path.write_text(
        json.dumps({"project_location": str(project_location)}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return SettingsHandler(store=SettingsStore(settings_path=settings_path))


def test_get_projects_contract_returns_project_list(tmp_path: Path) -> None:
    projects_root = tmp_path / "projects"
    projects_root.mkdir(parents=True)

    proj = projects_root / "video-1"
    proj.mkdir()
    (proj / "metadata.json").write_text(
        json.dumps(
            {
                "project_id": "video-1",
                "video_url": "https://www.youtube.com/watch?v=abc123",
                "created_date": "2026-04-28T10:00:00Z",
                "run_count": 2,
                "last_analyzed": "2026-04-28T11:00:00Z",
                "candidate_count_total": 15,
                "candidate_count_reviewed": 8,
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    handler = ProjectsHandler(
        project_service=ProjectService(),
        settings_handler=_make_settings_handler(tmp_path, projects_root),
    )
    status, body = handler.get_projects()

    assert status == 200
    assert body["location_status"] == "valid"
    assert len(body["projects"]) == 1
    assert body["projects"][0]["project_id"] == "video-1"


def test_get_projects_auto_creates_missing_location_and_returns_empty_list(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing-projects"
    handler = ProjectsHandler(
        project_service=ProjectService(),
        settings_handler=_make_settings_handler(tmp_path, missing_root),
    )

    status, body = handler.get_projects()
    assert status == 200
    assert body["location_status"] == "valid"
    assert body["projects"] == []
    assert missing_root.exists()


def test_put_settings_contract_validates_location(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    handler = SettingsHandler(store=SettingsStore(settings_path=settings_path))

    valid_path = tmp_path / "new-project-root"
    status, body = handler.put_settings({"project_location": str(valid_path)})
    assert status == 200
    assert body["project_location"] == str(valid_path)
    assert body["location_status"] == "valid"


def test_put_settings_rejects_unusable_path(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    handler = SettingsHandler(store=SettingsStore(settings_path=settings_path))

    # A file path cannot be created as a writable directory.
    blocked = tmp_path / "not-a-folder"
    blocked.write_text("x", encoding="utf-8")

    status, body = handler.put_settings({"project_location": str(blocked)})
    assert status == 422
    assert body["error"] == "invalid_project_location"


def test_delete_project_contract_removes_project_directory(tmp_path: Path) -> None:
    projects_root = tmp_path / "projects"
    projects_root.mkdir(parents=True)

    proj = projects_root / "video-delete-1"
    proj.mkdir()
    (proj / "metadata.json").write_text(
        json.dumps(
            {
                "project_id": "video-delete-1",
                "video_url": "https://www.youtube.com/watch?v=delete1",
                "created_date": "2026-04-28T10:00:00Z",
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    (proj / "result_0.review.json").write_text("{}", encoding="utf-8")

    handler = ProjectsHandler(
        project_service=ProjectService(),
        settings_handler=_make_settings_handler(tmp_path, projects_root),
    )

    status, body = handler.delete_project("video-delete-1")

    assert status == 200
    assert body["project_id"] == "video-delete-1"
    assert body["deleted"] is True
    assert not proj.exists()


def test_delete_project_contract_returns_404_for_missing_project(tmp_path: Path) -> None:
    projects_root = tmp_path / "projects"
    projects_root.mkdir(parents=True)

    handler = ProjectsHandler(
        project_service=ProjectService(),
        settings_handler=_make_settings_handler(tmp_path, projects_root),
    )

    status, body = handler.delete_project("missing-project")
    assert status == 404
    assert body["error"] == "project_not_found"
