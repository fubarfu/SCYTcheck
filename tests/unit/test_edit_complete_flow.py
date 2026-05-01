"""
Test the complete edit flow to verify:
1. Edit action preserves prior decision status
2. Corrected text is shown in merged context
3. Status chip displays preserved status, not 'Edited'
"""

import json
from pathlib import Path
from src.services.review_service import ReviewService


def _write_sidecar(path: Path, video_url: str, candidates: list[dict]) -> None:
    """Write a test sidecar review file."""
    sidecar = {
        "url": video_url,
        "run_id": "run_1",
        "candidates": candidates,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")


def test_edit_preserves_unreviewed_status_and_shows_text(tmp_path: Path) -> None:
    """
    Test that editing an unreviewed candidate:
    1. Preserves the 'unreviewed' (pending) status
    2. Stores the corrected text
    3. Merged context returns both correctly
    4. Status chip should not show 'Edited', but the text should be the corrected text
    """
    project_root = tmp_path / "projects"
    video_id = "test_edit_unreviewed"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    # Create initial candidate
    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=test_edit",
        [{"candidate_id": "cand-1", "extracted_name": "OriginalName"}],
    )

    service = ReviewService()

    # Verify initial state - unreviewed
    merged = service.merge_review_context(str(project_root), video_id)
    candidate = next(c for c in merged["candidates"] if c["id"] == "cand-1")
    assert candidate["decision"] == "unreviewed", "Initial state should be unreviewed"
    assert candidate["corrected_text"] == "", "No corrected text initially"
    assert candidate["spelling"] == "OriginalName"

    # Apply edit action
    result = service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="edited",
        user_note="CorrectedName",
    )

    # Check immediate return value
    assert result["decision"] == "unreviewed", f"apply_candidate_action should return unreviewed, not {result['decision']}"

    # Reload and verify merged context
    merged = service.merge_review_context(str(project_root), video_id)
    candidate = next(c for c in merged["candidates"] if c["id"] == "cand-1")

    # Verify status is NOT changed to "edited"
    assert candidate["decision"] == "unreviewed", f"Status should remain unreviewed after edit, got {candidate['decision']}"

    # Verify corrected text is surfaced
    assert candidate["corrected_text"] == "CorrectedName", f"Corrected text should be 'CorrectedName', got {candidate.get('corrected_text')}"

    # Verify the display text would use corrected_text
    display_text = candidate.get("corrected_text") or candidate.get("spelling")
    assert display_text == "CorrectedName", f"Display should show corrected text, got {display_text}"


def test_edit_preserves_confirmed_status_and_shows_text(tmp_path: Path) -> None:
    """
    Test that editing a confirmed candidate:
    1. Preserves the 'confirmed' status
    2. Stores the corrected text
    3. Merged context returns both
    """
    project_root = tmp_path / "projects"
    video_id = "test_edit_confirmed"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=test_confirmed",
        [{"candidate_id": "cand-1", "extracted_name": "OriginalName"}],
    )

    service = ReviewService()

    # First confirm the candidate
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="confirmed",
    )

    merged = service.merge_review_context(str(project_root), video_id)
    candidate = next(c for c in merged["candidates"] if c["id"] == "cand-1")
    assert candidate["decision"] == "confirmed"

    # Now edit it
    result = service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="edited",
        user_note="BetterName",
    )

    # Should return confirmed, not edited
    assert result["decision"] == "confirmed", f"Status should remain confirmed after edit, got {result['decision']}"

    # Reload and verify
    merged = service.merge_review_context(str(project_root), video_id)
    candidate = next(c for c in merged["candidates"] if c["id"] == "cand-1")

    assert candidate["decision"] == "confirmed", f"Confirmed status should be preserved, got {candidate['decision']}"
    assert candidate["corrected_text"] == "BetterName", f"Corrected text should be updated, got {candidate.get('corrected_text')}"

    display_text = candidate.get("corrected_text") or candidate.get("spelling")
    assert display_text == "BetterName", f"Display should show corrected text, got {display_text}"


def test_edit_preserves_rejected_status_and_shows_text(tmp_path: Path) -> None:
    """Test that editing a rejected candidate preserves rejected status."""
    project_root = tmp_path / "projects"
    video_id = "test_edit_rejected"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=test_rejected",
        [
            {"candidate_id": "cand-1", "extracted_name": "Name1", "spelling": "Name1"},
            {"candidate_id": "cand-2", "extracted_name": "Name2", "spelling": "Name2"},
        ],
    )

    service = ReviewService()

    # Reject cand-1
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="rejected",
    )

    # Edit cand-1
    result = service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="edited",
        user_note="EditedName",
    )

    # Status should remain rejected
    assert result["decision"] == "rejected", f"Rejected status should be preserved, got {result['decision']}"

    # Verify in merged
    merged = service.merge_review_context(str(project_root), video_id)
    candidate = next(c for c in merged["candidates"] if c["id"] == "cand-1")
    assert candidate["decision"] == "rejected"
    assert candidate["corrected_text"] == "EditedName"
