from __future__ import annotations

import json
from pathlib import Path

import pytest

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


def test_confirm_action_propagates_group_selection_semantics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-group-confirm"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=group-confirm",
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

    state_path = workspace / ".scyt_review_workspaces" / "review_state.json"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    decisions = payload["candidate_decisions"]
    assert decisions["cand-a"]["decision"] == "confirmed"
    assert decisions["cand-b"]["decision"] == "rejected"
    assert decisions["cand-c"]["decision"] == "rejected"


def test_reject_action_rejects_same_spelling_in_group(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-group-reject"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=group-reject",
        [{"candidate_id": "seed", "extracted_name": "Seed"}],
    )

    def _merge_with_duplicates(_: list[dict[str, object]], __: dict[str, dict[str, object]]) -> list[dict[str, object]]:
        return [
            {"id": "cand-a1", "spelling": "Alpha", "discovered_in_run": "0", "marked_new": False, "decision": "unreviewed", "frame_count": 0, "frame_samples": []},
            {"id": "cand-a2", "spelling": "Alpha", "discovered_in_run": "0", "marked_new": False, "decision": "unreviewed", "frame_count": 0, "frame_samples": []},
            {"id": "cand-b", "spelling": "Beta", "discovered_in_run": "0", "marked_new": False, "decision": "unreviewed", "frame_count": 0, "frame_samples": []},
        ]

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

    monkeypatch.setattr(ReviewService, "_merge_candidates", staticmethod(_merge_with_duplicates))
    monkeypatch.setattr("src.services.review_service.recompute_groups", _group_all)

    service = ReviewService()
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-a1",
        action="rejected",
    )

    state_path = workspace / ".scyt_review_workspaces" / "review_state.json"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    decisions = payload["candidate_decisions"]
    assert decisions["cand-a1"]["decision"] == "rejected"
    assert decisions["cand-a2"]["decision"] == "rejected"
    assert "cand-b" not in decisions


def test_edited_action_surfaces_corrected_text_in_merged_context(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-edited-name"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=edited-name",
        [{"candidate_id": "cand-1", "extracted_name": "CridI"}],
    )

    service = ReviewService()
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="edited",
        user_note="Cridi",
    )

    merged = service.merge_review_context(str(project_root), video_id)
    candidate = next(c for c in merged["candidates"] if c["id"] == "cand-1")

    assert candidate["decision"] == "unreviewed"
    assert candidate["spelling"] == "CridI"
    assert candidate["corrected_text"] == "Cridi"


def test_edited_action_preserves_confirmed_status(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-edited-preserves-status"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=edited-preserves-status",
        [{"candidate_id": "cand-1", "extracted_name": "CridI"}],
    )

    service = ReviewService()
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="confirmed",
    )
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="edited",
        user_note="Cridi",
    )

    merged = service.merge_review_context(str(project_root), video_id)
    candidate = next(c for c in merged["candidates"] if c["id"] == "cand-1")

    assert candidate["decision"] == "confirmed"
    assert candidate["corrected_text"] == "Cridi"


def test_legacy_edited_decision_is_normalized_and_name_is_preserved(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-legacy-edited"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=legacy-edited",
        [{"candidate_id": "cand-1", "extracted_name": "Grynal"}],
    )

    legacy_state_dir = workspace / ".scyt_review_workspaces"
    legacy_state_dir.mkdir(parents=True, exist_ok=True)
    (legacy_state_dir / "review_state.json").write_text(
        json.dumps(
            {
                "candidate_decisions": {
                    "cand-1": {
                        "decision": "edited",
                        "marked_new": False,
                        "user_note": "Grynsi",
                    }
                }
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    service = ReviewService()

    merged = service.merge_review_context(str(project_root), video_id)
    candidate = next(c for c in merged["candidates"] if c["id"] == "cand-1")
    assert candidate["decision"] == "unreviewed"
    assert candidate["corrected_text"] == "Grynsi"

    result = service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="edited",
        user_note="Grynal Fixed",
    )
    assert result["decision"] == "unreviewed"

    merged_after = service.merge_review_context(str(project_root), video_id)
    candidate_after = next(c for c in merged_after["candidates"] if c["id"] == "cand-1")
    assert candidate_after["decision"] == "unreviewed"
    assert candidate_after["corrected_text"] == "Grynal Fixed"


def test_edit_does_not_rename_group_display_name(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-group-name-stability"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=group-name-stability",
        [{"candidate_id": "cand-1", "extracted_name": "Grynal"}],
    )

    service = ReviewService()
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="edited",
        user_note="Grynal Corrected",
    )

    merged = service.merge_review_context(str(project_root), video_id)
    candidate = next(c for c in merged["candidates"] if c["id"] == "cand-1")
    assert candidate["corrected_text"] == "Grynal Corrected"

    group = next(g for g in merged["groups"] if "cand-1" in g["candidate_ids"])
    assert group["name"] == "Grynal"


def test_edited_name_persists_after_reject_action(tmp_path: Path) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-edited-then-rejected"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=edited-then-rejected",
        [{"candidate_id": "cand-1", "extracted_name": "Grynal"}],
    )

    service = ReviewService()
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="edited",
        user_note="Grynsi",
    )
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="rejected",
    )

    merged = service.merge_review_context(str(project_root), video_id)
    candidate = next(c for c in merged["candidates"] if c["id"] == "cand-1")

    assert candidate["decision"] == "rejected"
    assert candidate["corrected_text"] == "Grynsi"


def test_accepted_group_name_prefers_confirmed_edited_text(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / "projects"
    video_id = "video-accepted-uses-edited-name"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=accepted-uses-edited-name",
        [
            {"candidate_id": "cand-a", "extracted_name": "Grynal"},
            {"candidate_id": "cand-b", "extracted_name": "Grynol"},
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
        group_name = str(grouped_candidates[0].get("extracted_name") or "group") if grouped_candidates else "group"
        return {
            "candidates": grouped_candidates,
            "groups": [
                {
                    "group_id": "grp-1",
                    "display_name": group_name,
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
        action="edited",
        user_note="Grynsi",
    )
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-a",
        action="confirmed",
    )

    merged = service.merge_review_context(str(project_root), video_id)
    candidate = next(c for c in merged["candidates"] if c["id"] == "cand-a")
    group = next(g for g in merged["groups"] if "cand-a" in g["candidate_ids"])

    assert candidate["decision"] == "confirmed"
    assert candidate["corrected_text"] == "Grynsi"
    assert group["name"] == "Grynsi"
