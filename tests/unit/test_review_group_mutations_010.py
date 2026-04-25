from __future__ import annotations

from src.web.app.group_mutation_service import GroupMutationService


def _group_payload() -> dict:
    return {
        "groups": [
            {
                "group_id": "grp_1",
                "candidates": [
                    {"candidate_id": "c1", "extracted_name": "Alice", "status": "pending"},
                    {"candidate_id": "c2", "extracted_name": "Alicia", "status": "pending"},
                ],
            }
        ],
        "candidates": [
            {"candidate_id": "c1", "extracted_name": "Alice", "status": "pending"},
            {"candidate_id": "c2", "extracted_name": "Alicia", "status": "pending"},
        ],
        "accepted_names": {},
        "rejected_candidates": {},
        "collapsed_groups": {},
        "resolution_status": {},
    }


def test_confirm_sets_accepted_name_and_resolved_state() -> None:
    payload, validation, handled = GroupMutationService.confirm_candidate(_group_payload(), "grp_1", "c1")

    assert handled is True
    assert validation == {"is_valid": True, "candidate_name": "Alice"}
    assert payload["accepted_names"]["grp_1"] == "Alice"
    assert payload["resolution_status"]["grp_1"] == "RESOLVED"
    assert payload["collapsed_groups"]["grp_1"] is True


def test_rejecting_currently_accepted_candidate_clears_group_resolution() -> None:
    starting, _, _ = GroupMutationService.confirm_candidate(_group_payload(), "grp_1", "c1")

    payload, validation, handled = GroupMutationService.reject_candidate(starting, "grp_1", "c1")

    assert handled is True
    assert validation is None
    assert payload["accepted_names"]["grp_1"] == "Alicia"
    assert payload["resolution_status"]["grp_1"] == "RESOLVED"
    assert payload["collapsed_groups"]["grp_1"] is True
    assert payload["rejected_candidates"]["grp_1"] == ["c1"]
    assert payload["candidates"][0]["status"] == "rejected"


def test_unreject_restores_candidate_to_pending_without_forcing_acceptance() -> None:
    rejected, _, _ = GroupMutationService.reject_candidate(_group_payload(), "grp_1", "c2")

    payload, validation, handled = GroupMutationService.unreject_candidate(rejected, "grp_1", "c2")

    assert handled is True
    assert validation is None
    assert payload["rejected_candidates"].get("grp_1") is None
    candidate = next(item for item in payload["candidates"] if item["candidate_id"] == "c2")
    assert candidate["status"] == "pending"


def test_deselect_clears_accepted_name_and_expands_group() -> None:
    starting, _, _ = GroupMutationService.confirm_candidate(_group_payload(), "grp_1", "c1")

    payload, validation, handled = GroupMutationService.deselect_group(starting, "grp_1")

    assert handled is True
    assert validation is None
    assert payload["accepted_names"].get("grp_1") is None
    assert payload["resolution_status"]["grp_1"] == "UNRESOLVED"
    assert payload["collapsed_groups"]["grp_1"] is False


def test_consensus_transition_auto_collapses_after_reject_then_confirm() -> None:
    starting = _group_payload()

    after_reject, _, _ = GroupMutationService.reject_candidate(starting, "grp_1", "c2")
    after_confirm, validation, handled = GroupMutationService.confirm_candidate(after_reject, "grp_1", "c1")

    assert handled is True
    assert validation == {"is_valid": True, "candidate_name": "Alice"}
    assert after_confirm["accepted_names"]["grp_1"] == "Alice"
    assert after_confirm["rejected_candidates"]["grp_1"] == ["c2"]
    assert after_confirm["resolution_status"]["grp_1"] == "RESOLVED"
    assert after_confirm["collapsed_groups"]["grp_1"] is True
