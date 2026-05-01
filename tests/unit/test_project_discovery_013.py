from __future__ import annotations

import json
from pathlib import Path

from src.services.project_service import ProjectService


def _write_metadata(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def test_discover_projects_finds_valid_metadata_only(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    root.mkdir(parents=True)

    valid = root / "valid-project"
    valid.mkdir()
    _write_metadata(
        valid / "metadata.json",
        {
            "project_id": "valid-project",
            "video_url": "https://www.youtube.com/watch?v=ok",
            "created_date": "2026-04-28T10:00:00Z",
            "run_count": 1,
        },
    )

    missing_meta = root / "missing-meta"
    missing_meta.mkdir()

    invalid_meta = root / "invalid-meta"
    invalid_meta.mkdir()
    (invalid_meta / "metadata.json").write_text("[]", encoding="utf-8")

    service = ProjectService()
    projects = service.discover_projects(str(root))

    assert len(projects) == 1
    assert projects[0]["project_id"] == "valid-project"


def test_discover_projects_skips_corrupted_metadata(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    root.mkdir(parents=True)

    bad = root / "broken"
    bad.mkdir()
    (bad / "metadata.json").write_text("{not-json", encoding="utf-8")

    service = ProjectService()
    projects = service.discover_projects(str(root))
    assert projects == []


def test_discover_projects_sorts_newest_first(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    root.mkdir(parents=True)

    old = root / "old"
    old.mkdir()
    _write_metadata(
        old / "metadata.json",
        {
            "project_id": "old",
            "video_url": "https://www.youtube.com/watch?v=old",
            "created_date": "2026-04-27T10:00:00Z",
            "run_count": 1,
        },
    )

    new = root / "new"
    new.mkdir()
    _write_metadata(
        new / "metadata.json",
        {
            "project_id": "new",
            "video_url": "https://www.youtube.com/watch?v=new",
            "created_date": "2026-04-28T10:00:00Z",
            "run_count": 1,
        },
    )

    projects = ProjectService().discover_projects(str(root))
    assert [p["project_id"] for p in projects] == ["new", "old"]


def test_discover_projects_in_legacy_hidden_workspace_root(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    legacy_root = root / ".scyt_review_workspaces"
    legacy_root.mkdir(parents=True)

    project_dir = legacy_root / "video-hidden"
    project_dir.mkdir()
    _write_metadata(
        project_dir / "metadata.json",
        {
            "project_id": "video-hidden",
            "video_url": "https://www.youtube.com/watch?v=hidden",
            "created_date": "2026-04-28T15:00:00Z",
            "run_count": 2,
        },
    )

    projects = ProjectService().discover_projects(str(root))

    assert len(projects) == 1
    assert projects[0]["project_id"] == "video-hidden"
    assert Path(projects[0]["project_location"]) == project_dir
