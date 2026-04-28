from __future__ import annotations

import json
from pathlib import Path

from src.services.review_service import ReviewService


def _write_sidecar(path: Path, source_value: str, candidates: list[dict[str, object]]) -> None:
    payload = {
        "source_value": source_value,
        "candidates": candidates,
    }
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def test_mark_new_only_for_spellings_unique_to_latest_run(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-1"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=old",
        [
            {"candidate_id": "cand-old", "extracted_name": "Alpha"},
            {"candidate_id": "cand-shared", "extracted_name": "Beta"},
        ],
    )
    _write_sidecar(
        workspace / "result_2.review.json",
        "https://www.youtube.com/watch?v=old",
        [
            {"candidate_id": "cand-shared2", "extracted_name": "Beta"},
            {"candidate_id": "cand-new", "extracted_name": "Gamma"},
        ],
    )

    service = ReviewService()
    merged = service.merge_review_context(str(project_root), video_id)

    by_spelling = {c["spelling"]: c for c in merged["candidates"]}
    assert by_spelling["Alpha"]["marked_new"] is False
    assert by_spelling["Beta"]["marked_new"] is False
    assert by_spelling["Gamma"]["marked_new"] is True


def test_redetected_spelling_is_not_marked_new(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-2"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=old",
        [{"candidate_id": "cand-1", "extracted_name": "RepeatName"}],
    )
    _write_sidecar(
        workspace / "result_2.review.json",
        "https://www.youtube.com/watch?v=old",
        [{"candidate_id": "cand-2", "extracted_name": "RepeatName"}],
    )

    service = ReviewService()
    merged = service.merge_review_context(str(project_root), video_id)

    assert len(merged["candidates"]) == 1
    assert merged["candidates"][0]["spelling"] == "RepeatName"
    assert merged["candidates"][0]["marked_new"] is False


def test_marked_new_clear_persists_after_user_action(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-3"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=old",
        [{"candidate_id": "cand-old", "extracted_name": "OldName"}],
    )
    _write_sidecar(
        workspace / "result_2.review.json",
        "https://www.youtube.com/watch?v=old",
        [{"candidate_id": "cand-new", "extracted_name": "NewName"}],
    )

    service = ReviewService()

    # First merge marks NewName as fresh.
    initial = service.merge_review_context(str(project_root), video_id)
    new_candidate = next(c for c in initial["candidates"] if c["spelling"] == "NewName")
    assert new_candidate["marked_new"] is True

    # User action should clear freshness and persist it.
    action_result = service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id=str(new_candidate["id"]),
        action="clear_new",
    )
    assert action_result["marked_new"] is False

    merged_again = service.merge_review_context(str(project_root), video_id)
    again = next(c for c in merged_again["candidates"] if c["spelling"] == "NewName")
    assert again["marked_new"] is False

    state_path = workspace / ".scyt_review_workspaces" / "review_state.json"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["candidate_decisions"][str(new_candidate["id"])]["marked_new"] is False
