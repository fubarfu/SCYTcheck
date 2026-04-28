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


def test_multi_run_marks_only_latest_unique_spellings(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-integration-1"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=run1",
        [
            {"candidate_id": "a1", "extracted_name": "NameA"},
            {"candidate_id": "b1", "extracted_name": "NameB"},
        ],
    )
    _write_sidecar(
        workspace / "result_2.review.json",
        "https://www.youtube.com/watch?v=run1",
        [
            {"candidate_id": "b2", "extracted_name": "NameB"},
            {"candidate_id": "c2", "extracted_name": "NameC"},
        ],
    )

    merged = ReviewService().merge_review_context(str(project_root), video_id)
    assert merged["run_count"] == 2

    by_spelling = {c["spelling"]: c for c in merged["candidates"]}
    assert by_spelling["NameA"]["marked_new"] is False
    assert by_spelling["NameB"]["marked_new"] is False
    assert by_spelling["NameC"]["marked_new"] is True


def test_marker_clears_after_action_and_stays_cleared(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-integration-2"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=run2",
        [{"candidate_id": "legacy", "extracted_name": "LegacyName"}],
    )
    _write_sidecar(
        workspace / "result_2.review.json",
        "https://www.youtube.com/watch?v=run2",
        [{"candidate_id": "fresh", "extracted_name": "FreshName"}],
    )

    service = ReviewService()
    context = service.merge_review_context(str(project_root), video_id)
    fresh = next(c for c in context["candidates"] if c["spelling"] == "FreshName")
    assert fresh["marked_new"] is True

    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id=str(fresh["id"]),
        action="confirmed",
    )

    context_after = service.merge_review_context(str(project_root), video_id)
    fresh_after = next(c for c in context_after["candidates"] if c["spelling"] == "FreshName")
    assert fresh_after["marked_new"] is False
    assert fresh_after["decision"] == "confirmed"
