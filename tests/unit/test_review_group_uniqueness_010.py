from __future__ import annotations

from src.web.app.group_mutation_service import GroupMutationService


def _payload_with_duplicate_conflict() -> dict:
    return {
        "groups": [
            {
                "group_id": "grp_1",
                "candidates": [
                    {"candidate_id": "g1_c1", "extracted_name": "Alice", "status": "confirmed"},
                ],
            },
            {
                "group_id": "grp_2",
                "candidates": [
                    {"candidate_id": "g2_c1", "extracted_name": "Alice", "status": "pending"},
                    {"candidate_id": "g2_c2", "extracted_name": "Alicia", "status": "pending"},
                ],
            },
        ],
        "candidates": [
            {"candidate_id": "g1_c1", "extracted_name": "Alice", "status": "confirmed"},
            {"candidate_id": "g2_c1", "extracted_name": "Alice", "status": "pending"},
            {"candidate_id": "g2_c2", "extracted_name": "Alicia", "status": "pending"},
        ],
        "accepted_names": {"grp_1": "Alice"},
        "rejected_candidates": {},
        "collapsed_groups": {"grp_1": True, "grp_2": False},
        "resolution_status": {"grp_1": "RESOLVED", "grp_2": "UNRESOLVED"},
    }


def test_confirm_candidate_blocks_duplicate_accepted_name_across_groups() -> None:
    payload, validation, handled = GroupMutationService.confirm_candidate(
        _payload_with_duplicate_conflict(),
        "grp_2",
        "g2_c1",
    )

    assert handled is True
    assert validation is not None
    assert validation["is_valid"] is False
    assert validation["candidate_name"] == "Alice"
    assert validation["conflict_group_id"] == "grp_1"
    assert validation["message"] == "Accepted name already used by group grp_1"
    assert validation["hint"] == "Choose a different candidate in this group"
    assert payload["accepted_names"] == {"grp_1": "Alice"}
    assert payload["accepted_names"].get("grp_2") is None


def test_confirm_candidate_duplicate_check_is_case_insensitive() -> None:
    starting = _payload_with_duplicate_conflict()
    starting["accepted_names"] = {"grp_1": "ALICE"}

    _, validation, handled = GroupMutationService.confirm_candidate(starting, "grp_2", "g2_c1")

    assert handled is True
    assert validation is not None
    assert validation["is_valid"] is False
    assert validation["conflict_group_id"] == "grp_1"
