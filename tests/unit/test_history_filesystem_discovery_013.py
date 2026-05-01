from __future__ import annotations

import json
from types import SimpleNamespace

from src.services.history_service import HistoryService
from src.services.project_service import ProjectService
from src.web.app.history_store import HistoryStore


def _settings_with_location(path: str) -> SimpleNamespace:
    return SimpleNamespace(project_location=path)


def test_list_videos_prefers_filesystem_project_discovery(tmp_path) -> None:
    projects_root = tmp_path / "projects"
    projects_root.mkdir(parents=True)

    project_a = projects_root / "video-a"
    project_a.mkdir()
    (project_a / "metadata.json").write_text(
        json.dumps(
            {
                "project_id": "video-a",
                "video_url": "https://www.youtube.com/watch?v=aaa",
                "created_date": "2026-04-28T10:00:00Z",
                "last_analyzed": "2026-04-28T10:10:00Z",
                "run_count": 2,
            }
        ),
        encoding="utf-8",
    )

    # Legacy history index contains unrelated stale entry; list should prefer filesystem projects.
    index_path = tmp_path / "video_history.json"
    store = HistoryStore(index_path=index_path)
    store.upsert_entry(
        {
            "history_id": "legacy-1",
            "display_name": "legacy",
            "canonical_source": "legacy",
            "duration_seconds": 12,
            "potential_duplicate": False,
            "run_count": 1,
            "output_folder": str(tmp_path / "legacy"),
            "deleted": False,
        }
    )

    service = HistoryService(
        store=store,
        project_service=ProjectService(),
        settings_loader=lambda: _settings_with_location(str(projects_root)),
    )

    body = service.list_videos()
    assert body["total"] == 1
    assert body["items"][0]["history_id"] == "video-a"
    assert body["items"][0]["run_count"] == 2
    assert body["items"][0]["output_folder"] == str(project_a)


def test_reopen_accepts_project_id_from_filesystem_discovery(tmp_path) -> None:
    projects_root = tmp_path / "projects"
    projects_root.mkdir(parents=True)

    project_a = projects_root / "video-a"
    project_a.mkdir()
    (project_a / "metadata.json").write_text(
        json.dumps(
            {
                "project_id": "video-a",
                "video_url": "https://www.youtube.com/watch?v=aaa",
                "created_date": "2026-04-28T10:00:00Z",
                "last_analyzed": "2026-04-28T10:10:00Z",
                "run_count": 2,
            }
        ),
        encoding="utf-8",
    )

    service = HistoryService(
        store=HistoryStore(index_path=tmp_path / "video_history.json"),
        project_service=ProjectService(),
        settings_loader=lambda: _settings_with_location(str(projects_root)),
    )

    reopen = service.reopen("video-a")

    assert reopen["history_id"] == "video-a"
    assert reopen["analysis_context"]["source_type"] == "youtube_url"
    assert reopen["analysis_context"]["source_value"] == "https://www.youtube.com/watch?v=aaa"
    assert reopen["review_route"] == "/review?video_id=video-a"
