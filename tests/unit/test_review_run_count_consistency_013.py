from __future__ import annotations

import json
from pathlib import Path

from src.services.review_service import ReviewService


def test_merge_review_context_uses_metadata_run_count_when_higher(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "vid_abc"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    (workspace / "metadata.json").write_text(
        json.dumps(
            {
                "project_id": video_id,
                "video_url": "https://www.youtube.com/watch?v=abc",
                "run_count": 2,
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Only one sidecar exists, but metadata reports 2 analysis runs.
    (workspace / "result_0.review.json").write_text(
        json.dumps(
            {
                "source_value": "https://www.youtube.com/watch?v=abc",
                "candidates": [],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = ReviewService().merge_review_context(str(project_root), video_id)

    assert payload["run_count"] == 2
    assert payload["latest_run_id"] == "1"
