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


def test_selection_reset_clears_group_candidate_decisions(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-selection-reset"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=selection-reset",
        [
            {"candidate_id": "cand-a", "extracted_name": "Alpha"},
            {"candidate_id": "cand-b", "extracted_name": "Beta"},
            {"candidate_id": "cand-c", "extracted_name": "Gamma"},
        ],
    )

    def _group_all(payload: dict[str, object]) -> dict[str, object]:
        incoming = list(payload.get("candidates") or [])
        grouped_candidates = [
            {
                "candidate_id": str(candidate.get("candidate_id") or ""),
                "extracted_name": str(candidate.get("extracted_name") or ""),
                "status": str(candidate.get("status") or "unreviewed"),
            }
            for candidate in incoming
        ]
        return {
            "candidates": grouped_candidates,
            "groups": [
                {
                    "group_id": "grp-1",
                    "display_name": "grp-1",
                    "candidates": [
                        {"candidate_id": str(candidate.get("candidate_id") or "")}
                        for candidate in grouped_candidates
                    ],
                }
            ],
        }

    monkeypatch.setattr("src.services.review_service.recompute_groups", _group_all)

    service = ReviewService()
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-a",
        action="confirmed",
    )

    for candidate_id in ["cand-a", "cand-b", "cand-c"]:
        service.apply_candidate_action(
            project_location=str(project_root),
            video_id=video_id,
            candidate_id=candidate_id,
            action="unreviewed",
        )

    state_path = workspace / ".scyt_review_workspaces" / "review_state.json"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    decisions = payload["candidate_decisions"]
    assert decisions["cand-a"]["decision"] == "unreviewed"
    assert decisions["cand-b"]["decision"] == "unreviewed"
    assert decisions["cand-c"]["decision"] == "unreviewed"


def test_grouping_recalculate_persists_thresholds_and_resets_decisions(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-grouping-recalculate"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=grouping-recalculate",
        [
            {"candidate_id": "cand-a", "extracted_name": "Alpha"},
            {"candidate_id": "cand-b", "extracted_name": "Alpah"},
        ],
    )

    service = ReviewService()
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-a",
        action="confirmed",
    )

    result = service.update_grouping_settings(
        project_location=str(project_root),
        video_id=video_id,
        thresholds={
            "similarity_threshold": 92,
            "recommendation_threshold": 65,
            "spelling_influence": 20,
            "temporal_influence": 80,
        },
        reset_decisions=True,
    )

    assert result["thresholds"]["similarity_threshold"] == 92
    assert result["thresholds"]["recommendation_threshold"] == 65
    assert result["thresholds"]["spelling_influence"] == 20
    assert result["thresholds"]["temporal_influence"] == 80

    state_path = workspace / ".scyt_review_workspaces" / "review_state.json"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload.get("candidate_decisions", {}) == {}