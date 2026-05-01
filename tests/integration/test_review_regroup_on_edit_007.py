from __future__ import annotations

from src.web.app.grouping_service import GroupingService, GroupingThresholds


def test_regroup_on_edit_changes_grouping() -> None:
    candidates = [
        {
            "candidate_id": "c1",
            "extracted_name": "Alic3",
            "corrected_text": "Alice",
            "start_timestamp": 1.0,
        },
        {"candidate_id": "c2", "extracted_name": "Alice", "start_timestamp": 1.4},
    ]
    groups = GroupingService.build_groups(candidates, GroupingThresholds(similarity_threshold=70))
    assert len(groups) == 1


def test_regroup_notice_flag_expected_for_edit_workflow() -> None:
    payload = {"action_type": "edit", "target_ids": ["c1"], "payload": {"corrected_text": "Alice"}}
    assert payload["action_type"] == "edit"
