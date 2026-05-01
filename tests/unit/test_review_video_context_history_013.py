from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from src.web.api.routes.review import ReviewHandler
from src.web.api.routes.review_history import ReviewHistoryHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.review_history_store import ReviewHistoryStore
from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.web.app.session_manager import SessionManager


def test_review_service_loads_hidden_workspace_project(tmp_path: Path) -> None:
    from src.services.review_service import ReviewService

    project_root = tmp_path / "projects"
    workspace_root = project_root / ".scyt_review_workspaces" / "vid_hidden"
    workspace_root.mkdir(parents=True)
    (workspace_root / "metadata.json").write_text(
        json.dumps(
            {
                "project_id": "vid_hidden",
                "video_url": "https://www.youtube.com/watch?v=hidden",
                "created_date": "2026-05-01T10:00:00Z",
                "run_count": 1,
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    (workspace_root / "result_0.review.json").write_text(
        json.dumps(
            {
                "video_url": "https://www.youtube.com/watch?v=hidden",
                "candidates": [
                    {
                        "id": "cand-1",
                        "extracted_name": "Player One",
                        "spelling": "Player One",
                        "decision": "unreviewed",
                        "start_timestamp": "00:01",
                    }
                ],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    context = ReviewService().merge_review_context(str(project_root), "vid_hidden")

    assert context["video_id"] == "vid_hidden"
    assert Path(context["project_location"]) == workspace_root
    assert len(context["candidates"]) == 1


class _FakeSettingsHandler:
    def __init__(self, project_location: Path) -> None:
        self._project_location = str(project_location)

    def get_settings(self) -> dict[str, Any]:
        return {"project_location": self._project_location}


class _FakeReviewService:
    def __init__(self, contexts: dict[str, dict[str, Any]]) -> None:
        self._contexts = contexts

    def merge_review_context(self, project_location: str, video_id: str) -> dict[str, Any]:
        del project_location
        context = self._contexts.get(video_id)
        if context is None:
            raise FileNotFoundError(video_id)
        return deepcopy(context)

    def apply_candidate_action(
        self,
        project_location: str,
        video_id: str,
        candidate_id: str,
        action: str,
        user_note: str | None = None,
    ) -> dict[str, Any]:
        del project_location, user_note
        context = self._contexts.get(video_id)
        if context is None:
            raise FileNotFoundError(video_id)
        for candidate in context.get("candidates", []):
            if candidate.get("id") == candidate_id:
                candidate["decision"] = action
                break
        return {
            "candidate_id": candidate_id,
            "decision": action,
            "marked_new": False,
        }

    def update_grouping_settings(
        self,
        project_location: str,
        video_id: str,
        thresholds: dict[str, Any],
        *,
        reset_decisions: bool,
    ) -> dict[str, Any]:
        del project_location, reset_decisions
        context = self._contexts.get(video_id)
        if context is None:
            raise FileNotFoundError(video_id)
        context["thresholds"] = dict(thresholds)
        return deepcopy(context)


def _make_context(workspace_root: Path, video_id: str, run_count: int) -> dict[str, Any]:
    return {
        "video_id": video_id,
        "video_url": f"https://youtube.com/watch?v={video_id}",
        "project_location": str(workspace_root),
        "run_count": run_count,
        "latest_run_id": str(max(0, run_count - 1)),
        "candidates": [
            {
                "id": "cand_1",
                "spelling": "Alice",
                "corrected_text": None,
                "decision": "unreviewed",
                "marked_new": False,
                "start_timestamp": "00:00:01.000",
            }
        ],
        "groups": [
            {
                "id": "grp_1",
                "name": "Alice",
                "candidate_ids": ["cand_1"],
                "decision": "confirmed",
            }
        ],
        "thresholds": {
            "similarity_threshold": 80,
            "recommendation_threshold": 70,
            "spelling_influence": 50,
            "temporal_influence": 50,
            "temporal_window_seconds": 2.0,
        },
    }


def test_video_context_switch_creates_history_entry(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    workspace_a = project_root / "video_a"
    workspace_b = project_root / "video_b"
    workspace_a.mkdir(parents=True, exist_ok=True)
    workspace_b.mkdir(parents=True, exist_ok=True)
    (workspace_a / "result_latest.csv").write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")
    (workspace_b / "result_latest.csv").write_text("PlayerName,StartTimestamp\nBob,00:00:02.000\n", encoding="utf-8")

    sidecar = ReviewSidecarStore()
    history_store = ReviewHistoryStore(sidecar)
    sessions = SessionManager()
    review = ReviewHandler(
        review_service=_FakeReviewService(
            {
                "video_a": _make_context(workspace_a, "video_a", 1),
                "video_b": _make_context(workspace_b, "video_b", 1),
            }
        ),
        settings_handler=_FakeSettingsHandler(project_root),
        session_manager=sessions,
        history_store=history_store,
    )
    history = ReviewHistoryHandler(session_manager=sessions, history_store=history_store)

    status_a, _ = review.get_review_context({"video_id": "video_a"})
    assert status_a == 200
    status_b, _ = review.get_review_context({"video_id": "video_b"})
    assert status_b == 200

    list_status, list_body = history.get_history("video_a", session_id="video_a")
    assert list_status == 200
    assert len(list_body["entries"]) == 1
    assert list_body["entries"][0]["trigger_type"] == "video-switch"


def test_video_context_browser_close_creates_history_entry(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    workspace = project_root / "video_a"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "result_latest.csv").write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    sidecar = ReviewSidecarStore()
    history_store = ReviewHistoryStore(sidecar)
    sessions = SessionManager()
    review = ReviewHandler(
        review_service=_FakeReviewService({"video_a": _make_context(workspace, "video_a", 1)}),
        settings_handler=_FakeSettingsHandler(project_root),
        session_manager=sessions,
        history_store=history_store,
    )
    review_sessions = ReviewSessionHandler(session_manager=sessions, history_store=history_store)
    history = ReviewHistoryHandler(session_manager=sessions, history_store=history_store)

    status, _ = review.get_review_context({"video_id": "video_a"})
    assert status == 200

    close_status, close_body = review_sessions.post_flush_on_close("video_a")
    assert close_status == 200
    assert close_body["flushed"] is True

    list_status, list_body = history.get_history("video_a", session_id="video_a")
    assert list_status == 200
    assert len(list_body["entries"]) == 1
    assert list_body["entries"][0]["trigger_type"] == "browser-close"


def test_video_context_run_count_increase_creates_merge_history_entry(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    workspace = project_root / "video_a"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "result_latest.csv").write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    context = _make_context(workspace, "video_a", 1)
    sidecar = ReviewSidecarStore()
    history_store = ReviewHistoryStore(sidecar)
    sessions = SessionManager()
    review = ReviewHandler(
        review_service=_FakeReviewService({"video_a": context}),
        settings_handler=_FakeSettingsHandler(project_root),
        session_manager=sessions,
        history_store=history_store,
    )
    history = ReviewHistoryHandler(session_manager=sessions, history_store=history_store)

    status_1, _ = review.get_review_context({"video_id": "video_a"})
    assert status_1 == 200

    context["run_count"] = 2
    context["latest_run_id"] = "1"
    status_2, _ = review.get_review_context({"video_id": "video_a"})
    assert status_2 == 200

    list_status, list_body = history.get_history("video_a", session_id="video_a")
    assert list_status == 200
    assert len(list_body["entries"]) == 1
    assert list_body["entries"][0]["trigger_type"] == "analysis-merge"


def test_video_context_repeated_context_load_does_not_create_merge_snapshot_without_new_run(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    workspace = project_root / "video_a"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "result_latest.csv").write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    context = _make_context(workspace, "video_a", 3)
    sidecar = ReviewSidecarStore()
    history_store = ReviewHistoryStore(sidecar)
    sessions = SessionManager()
    review = ReviewHandler(
        review_service=_FakeReviewService({"video_a": context}),
        settings_handler=_FakeSettingsHandler(project_root),
        session_manager=sessions,
        history_store=history_store,
    )
    history = ReviewHistoryHandler(session_manager=sessions, history_store=history_store)

    status_1, _ = review.get_review_context({"video_id": "video_a"})
    assert status_1 == 200
    status_2, _ = review.get_review_context({"video_id": "video_a"})
    assert status_2 == 200

    list_status, list_body = history.get_history("video_a", session_id="video_a")
    assert list_status == 200
    assert len(list_body["entries"]) == 0
