"""
End-to-end test simulating the exact UI flow:
1. UI loads review context (gets merged candidates)
2. UI shows candidate with status="pending" (unreviewed)
3. User clicks edit, enters new text
4. UI sends action="edited" with corrected_text
5. UI reloads context
6. UI should show candidate with:
   - status="pending" (NOT "edited")
   - corrected_text displayed instead of extracted_name
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


def test_ui_flow_for_editing_unreviewed_candidate(tmp_path: Path) -> None:
    """
    Simulate the exact UI flow:
    Step 1: Initial load - candidate is unreviewed/pending
    Step 2: User edits and submits
    Step 3: Reload - verify status remains pending and corrected text shows
    """
    project_root = tmp_path / "projects"
    video_id = "ui_flow_test"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    # Setup: Create candidates
    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=test_ui_flow",
        [
            {"candidate_id": "cand-1", "extracted_name": "BadOCR"},
            {"candidate_id": "cand-2", "extracted_name": "AnotherBadOCR"},
        ],
    )

    service = ReviewService()

    # STEP 1: UI loads review context
    context_1 = service.merge_review_context(str(project_root), video_id)
    candidates_1 = {c["id"]: c for c in context_1["candidates"]}

    # Verify cand-1 is unreviewed
    cand1_1 = candidates_1["cand-1"]
    assert cand1_1["decision"] == "unreviewed", f"Initial decision should be unreviewed, got {cand1_1['decision']}"

    # Verify status maps to "pending" on frontend
    frontend_status_1 = "pending" if cand1_1["decision"] == "unreviewed" or not cand1_1["decision"] else cand1_1["decision"]
    assert frontend_status_1 == "pending", f"Frontend should show pending initially, got {frontend_status_1}"

    # Verify text shown would be extracted_name (no corrected_text yet)
    display_text_1 = cand1_1.get("corrected_text") or cand1_1.get("spelling")
    assert display_text_1 == "BadOCR", f"Initial display should show BadOCR, got {display_text_1}"

    # STEP 2: User edits - frontend calls apply_candidate_action
    result = service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="edited",
        user_note="CorrectOCR",
    )

    # Verify apply_candidate_action returns unreviewed status
    assert result["decision"] == "unreviewed", f"apply_candidate_action should return unreviewed, not {result['decision']}"

    # STEP 3: UI reloads context
    context_2 = service.merge_review_context(str(project_root), video_id)
    candidates_2 = {c["id"]: c for c in context_2["candidates"]}

    cand1_2 = candidates_2["cand-1"]

    # Verify decision is still unreviewed
    assert cand1_2["decision"] == "unreviewed", f"Decision should still be unreviewed after edit, got {cand1_2['decision']}"

    # Verify frontend status is still "pending"
    frontend_status_2 = "pending" if cand1_2["decision"] == "unreviewed" or not cand1_2["decision"] else cand1_2["decision"]
    assert frontend_status_2 == "pending", f"Status should still be pending after edit, got {frontend_status_2}"

    # Verify corrected_text is now shown
    display_text_2 = cand1_2.get("corrected_text") or cand1_2.get("spelling")
    assert display_text_2 == "CorrectOCR", f"Display should now show corrected text, got {display_text_2}"

    print("✓ UI flow test passed: Edited candidate maintains pending status and shows corrected text")


def test_ui_flow_with_confirmed_then_edited(tmp_path: Path) -> None:
    """
    Test confirming a candidate then editing it:
    1. Confirm candidate
    2. Edit candidate
    3. Verify status remains confirmed, not changed to edited
    4. Verify corrected text shows
    """
    project_root = tmp_path / "projects"
    video_id = "ui_flow_confirmed_edit"
    workspace = project_root / video_id
    workspace.mkdir(parents=True)

    _write_sidecar(
        workspace / "result_1.review.json",
        "https://www.youtube.com/watch?v=test_confirmed_edit",
        [{"candidate_id": "cand-1", "extracted_name": "Name"}],
    )

    service = ReviewService()

    # Confirm the candidate
    service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="confirmed",
    )

    context = service.merge_review_context(str(project_root), video_id)
    cand = next(c for c in context["candidates"] if c["id"] == "cand-1")
    assert cand["decision"] == "confirmed"

    # Now edit it
    result = service.apply_candidate_action(
        project_location=str(project_root),
        video_id=video_id,
        candidate_id="cand-1",
        action="edited",
        user_note="ImprovedName",
    )

    # Should return confirmed, not edited
    assert result["decision"] == "confirmed", f"Status after edit should remain confirmed, got {result['decision']}"

    # Reload and verify
    context = service.merge_review_context(str(project_root), video_id)
    cand = next(c for c in context["candidates"] if c["id"] == "cand-1")

    # Frontend would map confirmed to "confirmed" status
    frontend_status = cand["decision"]
    assert frontend_status == "confirmed", f"Frontend status should be confirmed, got {frontend_status}"

    # Corrected text should show
    display_text = cand.get("corrected_text") or cand.get("spelling")
    assert display_text == "ImprovedName", f"Should show corrected text, got {display_text}"

    print("✓ UI flow with confirmed-then-edit test passed")
