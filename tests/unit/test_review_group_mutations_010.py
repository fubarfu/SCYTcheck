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
    assert payload["rejected_candidates"]["grp_1"] == ["c2"]
    statuses = {item["candidate_id"]: item["status"] for item in payload["candidates"]}
    assert statuses["c1"] == "confirmed"
    assert statuses["c2"] == "rejected"


def test_confirm_accepts_all_same_spelling_and_rejects_different_spelling() -> None:
    payload = {
        "groups": [
            {
                "group_id": "grp_1",
                "candidates": [
                    {"candidate_id": "c1", "extracted_name": "Alice", "status": "pending"},
                    {"candidate_id": "c2", "extracted_name": "Alice", "status": "pending"},
                    {"candidate_id": "c3", "extracted_name": "Alicia", "status": "pending"},
                ],
            }
        ],
        "candidates": [
            {"candidate_id": "c1", "extracted_name": "Alice", "status": "pending"},
            {"candidate_id": "c2", "extracted_name": "Alice", "status": "pending"},
            {"candidate_id": "c3", "extracted_name": "Alicia", "status": "pending"},
        ],
        "accepted_names": {},
        "rejected_candidates": {},
        "collapsed_groups": {},
        "resolution_status": {},
    }

    confirmed, validation, handled = GroupMutationService.confirm_candidate(payload, "grp_1", "c1")

    assert handled is True
    assert validation == {"is_valid": True, "candidate_name": "Alice"}
    assert confirmed["accepted_names"]["grp_1"] == "Alice"
    assert confirmed["rejected_candidates"]["grp_1"] == ["c3"]
    statuses = {item["candidate_id"]: item["status"] for item in confirmed["candidates"]}
    assert statuses["c1"] == "confirmed"
    assert statuses["c2"] == "confirmed"
    assert statuses["c3"] == "rejected"


def test_reject_cascades_to_all_same_spelling_candidates() -> None:
    payload = {
        "groups": [
            {
                "group_id": "grp_1",
                "candidates": [
                    {"candidate_id": "c1", "extracted_name": "Alice", "status": "pending"},
                    {"candidate_id": "c2", "extracted_name": "Alice", "status": "pending"},
                    {"candidate_id": "c3", "extracted_name": "Alicia", "status": "pending"},
                ],
            }
        ],
        "candidates": [
            {"candidate_id": "c1", "extracted_name": "Alice", "status": "pending"},
            {"candidate_id": "c2", "extracted_name": "Alice", "status": "pending"},
            {"candidate_id": "c3", "extracted_name": "Alicia", "status": "pending"},
        ],
        "accepted_names": {},
        "rejected_candidates": {},
        "collapsed_groups": {},
        "resolution_status": {},
    }

    rejected, validation, handled = GroupMutationService.reject_candidate(payload, "grp_1", "c1")

    assert handled is True
    assert validation is None
    assert sorted(rejected["rejected_candidates"]["grp_1"]) == ["c1", "c2"]
    statuses = {item["candidate_id"]: item["status"] for item in rejected["candidates"]}
    assert statuses["c1"] == "rejected"
    assert statuses["c2"] == "rejected"
    assert statuses["c3"] == "pending"


def test_rejecting_currently_accepted_candidate_clears_group_resolution() -> None:
    starting, _, _ = GroupMutationService.confirm_candidate(_group_payload(), "grp_1", "c1")

    payload, validation, handled = GroupMutationService.reject_candidate(starting, "grp_1", "c1")

    assert handled is True
    assert validation is None
    assert payload["accepted_names"].get("grp_1") is None
    assert payload["resolution_status"]["grp_1"] == "UNRESOLVED"
    assert payload["collapsed_groups"]["grp_1"] is False
    assert payload["rejected_candidates"]["grp_1"] == ["c2", "c1"]
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
    assert payload["rejected_candidates"].get("grp_1") is None
    assert payload["resolution_status"]["grp_1"] == "UNRESOLVED"
    assert payload["collapsed_groups"]["grp_1"] is False
    statuses = {item["candidate_id"]: item["status"] for item in payload["candidates"]}
    assert statuses["c1"] == "pending"
    assert statuses["c2"] == "pending"


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


def test_move_candidate_sets_group_override_and_clears_source_consensus_if_moved_candidate_was_selected() -> None:
    starting, _, _ = GroupMutationService.confirm_candidate(_group_payload(), "grp_1", "c1")

    moved, validation, handled = GroupMutationService.move_candidate(starting, "c1", "grp_manual_1")

    assert handled is True
    assert validation is None
    assert moved["candidate_group_overrides"]["c1"] == "grp_manual_1"
    assert moved["accepted_names"].get("grp_1") is None
    assert "grp_1" not in moved["resolution_status"]


def test_move_candidate_recalculates_resolution_status_for_source_and_target_groups() -> None:
    payload = {
        "groups": [
            {
                "group_id": "grp_source",
                "candidates": [
                    {"candidate_id": "s1", "extracted_name": "Alice", "status": "pending"},
                    {"candidate_id": "s2", "extracted_name": "Alicia", "status": "pending"},
                ],
            },
            {
                "group_id": "grp_target",
                "candidates": [
                    {"candidate_id": "t1", "extracted_name": "Alice", "status": "pending"},
                ],
            },
        ],
        "candidates": [
            {"candidate_id": "s1", "extracted_name": "Alice", "status": "pending"},
            {"candidate_id": "s2", "extracted_name": "Alicia", "status": "pending"},
            {"candidate_id": "t1", "extracted_name": "Alice", "status": "pending"},
        ],
        "accepted_names": {"grp_target": "Alice"},
        "rejected_candidates": {},
        "collapsed_groups": {"grp_target": True},
        "resolution_status": {"grp_source": "UNRESOLVED", "grp_target": "RESOLVED"},
    }

    moved, validation, handled = GroupMutationService.move_candidate(payload, "s2", "grp_target")

    assert handled is True
    assert validation is None
    assert moved["candidate_group_overrides"]["s2"] == "grp_target"

    # Source and target existing groups are cleared so recompute can derive fresh status.
    assert "grp_source" not in moved["resolution_status"]
    assert "grp_target" not in moved["resolution_status"]
    assert "grp_target" not in moved["collapsed_groups"]


def test_merge_groups_sets_overrides_for_source_group_candidates() -> None:
    payload = {
        "groups": [
            {
                "group_id": "grp_1",
                "candidates": [{"candidate_id": "c1", "extracted_name": "Alice", "status": "pending"}],
            },
            {
                "group_id": "grp_2",
                "candidates": [{"candidate_id": "c2", "extracted_name": "Alicia", "status": "pending"}],
            },
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

    merged, validation, handled = GroupMutationService.merge_groups(payload, "grp_2", "grp_1")

    assert handled is True
    assert validation is None
    assert merged["candidate_group_overrides"]["c2"] == "grp_1"


def test_merge_groups_recalculates_target_resolution_status_after_membership_change() -> None:
    payload = {
        "groups": [
            {
                "group_id": "grp_1",
                "candidates": [{"candidate_id": "c1", "extracted_name": "Alice", "status": "pending"}],
            },
            {
                "group_id": "grp_2",
                "candidates": [{"candidate_id": "c2", "extracted_name": "Bob", "status": "pending"}],
            },
        ],
        "candidates": [
            {"candidate_id": "c1", "extracted_name": "Alice", "status": "pending"},
            {"candidate_id": "c2", "extracted_name": "Bob", "status": "pending"},
        ],
        "accepted_names": {"grp_1": "Alice", "grp_2": "Bob"},
        "rejected_candidates": {},
        "collapsed_groups": {"grp_1": True, "grp_2": True},
        "resolution_status": {"grp_1": "RESOLVED", "grp_2": "RESOLVED"},
    }

    merged, validation, handled = GroupMutationService.merge_groups(payload, "grp_2", "grp_1")

    assert handled is True
    assert validation is None
    assert "grp_2" not in merged["accepted_names"]
    assert "grp_2" not in merged["resolution_status"]
    assert "grp_1" not in merged["resolution_status"]
