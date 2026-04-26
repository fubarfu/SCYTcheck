from __future__ import annotations

import json
from pathlib import Path

from src.web.api.schemas import (
    ReviewActionRequestDTO,
    ReviewConfirmCandidateRequestDTO,
    ReviewToggleCollapseRequestDTO,
    SchemaValidationError,
)
from src.web.app.review_grouping import recompute_groups
from src.web.app.review_sidecar_store import ReviewSidecarStore

def _seed_payload() -> dict:
    return {
        "candidates": [
            {
                "candidate_id": "c1",
                "extracted_name": "Alice",
                "start_timestamp": "00:00:01.000",
                "status": "pending",
            },
            {
                "candidate_id": "c2",
                "extracted_name": "Alice",
                "start_timestamp": "00:00:01.300",
                "status": "pending",
            },
        ],
        "thresholds": {
            "similarity_threshold": 70,
            "recommendation_threshold": 60,
            "temporal_window_seconds": 3.0,
        },
        "accepted_names": {},
        "rejected_candidates": {},
        "collapsed_groups": {},
        "resolution_status": {},
    }


def test_review_sidecar_helpers_persist_group_state_maps(tmp_path: Path) -> None:
    csv_path = tmp_path / "result.csv"
    csv_path.write_text("PlayerName,StartTimestamp\nAlice,00:00:01.000\n", encoding="utf-8")

    store = ReviewSidecarStore()
    payload = _seed_payload()
    payload = recompute_groups(payload)
    group_id = payload["groups"][0]["group_id"]

    payload = store.set_group_accepted_name(payload, group_id, "Alice")
    payload = store.set_candidate_rejected(payload, group_id, "c2", True)
    payload = store.set_group_collapsed(payload, group_id, True)
    payload = store.set_group_resolution_status(payload, group_id, "RESOLVED")

    sidecar_path = store.save(csv_path, payload)
    loaded = store.load(csv_path)

    assert sidecar_path.exists()
    assert loaded is not None
    assert loaded["accepted_names"][group_id] == "Alice"
    assert loaded["rejected_candidates"][group_id] == ["c2"]
    assert loaded["collapsed_groups"][group_id] is True
    assert loaded["resolution_status"][group_id] == "RESOLVED"

    on_disk = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert "accepted_names" in on_disk
    assert "rejected_candidates" in on_disk


def test_recompute_groups_exact_match_consensus_defaults_to_resolved_and_collapsed() -> None:
    payload = recompute_groups(_seed_payload())

    assert len(payload["groups"]) == 1
    group = payload["groups"][0]
    group_id = group["group_id"]

    assert group["active_spellings"] == ["Alice"]
    assert group["resolution_status"] == "RESOLVED"
    assert group["accepted_name"] == "Alice"
    assert group["is_collapsed"] is True
    assert payload["accepted_names"][group_id] == "Alice"


def test_recompute_groups_respects_rejections_when_computing_consensus_state() -> None:
    payload = _seed_payload()
    payload["thresholds"]["similarity_threshold"] = 50
    payload["candidates"][1]["extracted_name"] = "Alyce"
    payload = recompute_groups(payload)
    assert len(payload["groups"]) == 1
    group = payload["groups"][0]
    group_id = group["group_id"]

    # Two active spellings => unresolved by default.
    assert group["resolution_status"] == "UNRESOLVED"
    assert group["is_collapsed"] is False

    payload["rejected_candidates"] = {group_id: ["c2"]}
    payload["resolution_status"] = {}
    payload = recompute_groups(payload)
    group = payload["groups"][0]
    assert group["resolution_status"] == "RESOLVED"
    assert group["accepted_name"] == "Alice"
    assert group["rejected_candidate_ids"] == ["c2"]


def test_recompute_groups_preserves_explicit_unresolved_override_for_single_spelling_group() -> None:
    payload = recompute_groups(_seed_payload())
    group = payload["groups"][0]
    group_id = group["group_id"]

    payload["accepted_names"] = {}
    payload["resolution_status"] = {group_id: "UNRESOLVED"}
    payload["collapsed_groups"] = {group_id: False}

    payload = recompute_groups(payload)
    group = payload["groups"][0]

    assert group["accepted_name"] is None
    assert group["resolution_status"] == "UNRESOLVED"
    assert group["is_collapsed"] is False


def test_review_action_dto_parity_for_confirmation_and_toggle() -> None:
    action = ReviewActionRequestDTO.from_payload(
        {
            "action_type": "confirm",
            "target_ids": ["c1"],
            "payload": {"group_id": "grp_1"},
        }
    )
    confirm = ReviewConfirmCandidateRequestDTO.from_action(action)
    toggle = ReviewToggleCollapseRequestDTO.from_payload({"group_id": "grp_1", "is_collapsed": True})

    assert action.action_type == "confirm"
    assert confirm.group_id == "grp_1"
    assert confirm.candidate_id == "c1"
    assert toggle.group_id == "grp_1"
    assert toggle.is_collapsed is True


def test_review_action_dto_rejects_invalid_confirm_payload() -> None:
    try:
        ReviewActionRequestDTO.from_payload(
            {
                "action_type": "confirm",
                "target_ids": [],
                "payload": {"group_id": "grp_1"},
            }
        )
    except SchemaValidationError as exc:
        assert "target_ids" in str(exc)
    else:
        raise AssertionError("Expected SchemaValidationError for empty confirm target_ids")
