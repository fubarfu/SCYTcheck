from __future__ import annotations

from typing import Any

from src.web.app.grouping_service import GroupingService, GroupingThresholds
from src.web.app.recommendation_service import RecommendationService
from src.web.app.review_sidecar_store import ReviewSidecarStore

DEFAULT_SIMILARITY_THRESHOLD = 80
DEFAULT_RECOMMENDATION_THRESHOLD = 70
DEFAULT_TEMPORAL_WINDOW_SECONDS = 2.0


def recompute_groups(session_payload: dict[str, Any]) -> dict[str, Any]:
    """Recompute review groups and recommendation metadata from current candidates."""
    payload = ReviewSidecarStore.ensure_group_state_maps(session_payload or {})
    thresholds = _normalize_thresholds(payload.get("thresholds", {}))
    candidates = list(payload.get("candidates", []))

    groups = GroupingService.build_groups(
        candidates,
        GroupingThresholds(
            similarity_threshold=thresholds["similarity_threshold"],
            temporal_window_seconds=thresholds["temporal_window_seconds"],
        ),
    )
    scored_groups = RecommendationService.score_groups(
        groups,
        recommendation_threshold=thresholds["recommendation_threshold"],
    )

    groups = _hydrate_group_state(payload, scored_groups)

    payload["thresholds"] = thresholds
    payload["groups"] = groups
    return payload


def _hydrate_group_state(payload: dict[str, Any], groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    accepted_map = dict(payload.get("accepted_names", {}))
    rejected_map = dict(payload.get("rejected_candidates", {}))
    collapsed_map = dict(payload.get("collapsed_groups", {}))

    hydrated: list[dict[str, Any]] = []
    normalized_accepted: dict[str, str] = {}
    normalized_rejected: dict[str, list[str]] = {}
    normalized_collapsed: dict[str, bool] = {}
    normalized_status: dict[str, str] = {}

    for raw_group in groups:
        group = dict(raw_group)
        group_id = str(group.get("group_id") or "")
        if not group_id:
            continue

        candidates = list(group.get("candidates", []))
        candidate_ids = {
            str(candidate.get("candidate_id", "")).strip()
            for candidate in candidates
            if str(candidate.get("candidate_id", "")).strip()
        }

        rejected_candidate_ids = [
            candidate_id
            for candidate_id in rejected_map.get(group_id, [])
            if candidate_id in candidate_ids
        ]
        normalized_rejected[group_id] = rejected_candidate_ids
        rejected_set = set(rejected_candidate_ids)

        active_candidates = [
            candidate
            for candidate in candidates
            if str(candidate.get("candidate_id", "")).strip() not in rejected_set
        ]
        active_spellings = sorted(
            {
                _candidate_name(candidate)
                for candidate in active_candidates
                if _candidate_name(candidate)
            }
        )

        accepted_name = str(accepted_map.get(group_id, "")).strip()
        if accepted_name and accepted_name not in active_spellings:
            accepted_name = ""
        if not accepted_name and len(active_spellings) == 1:
            accepted_name = active_spellings[0]

        if accepted_name:
            resolution_status = "RESOLVED"
        else:
            # Exact-match consensus is based on active candidates only.
            resolution_status = "RESOLVED" if len(active_spellings) == 1 and active_candidates else "UNRESOLVED"

        explicit_collapsed = collapsed_map.get(group_id)
        is_collapsed = bool(explicit_collapsed) if explicit_collapsed is not None else resolution_status == "RESOLVED"

        normalized_accepted[group_id] = accepted_name if accepted_name else ""
        normalized_collapsed[group_id] = is_collapsed
        normalized_status[group_id] = resolution_status

        group["accepted_name"] = accepted_name or None
        group["rejected_candidate_ids"] = rejected_candidate_ids
        group["is_collapsed"] = is_collapsed
        group["resolution_status"] = normalized_status[group_id]
        group["active_spellings"] = active_spellings
        group["active_candidate_count"] = len(active_candidates)
        group["total_candidate_count"] = len(candidates)
        hydrated.append(group)

    payload["accepted_names"] = {
        group_id: value for group_id, value in normalized_accepted.items() if value
    }
    payload["rejected_candidates"] = {
        group_id: value for group_id, value in normalized_rejected.items() if value
    }
    payload["collapsed_groups"] = normalized_collapsed
    payload["resolution_status"] = normalized_status
    return hydrated


def _candidate_name(candidate: dict[str, Any]) -> str:
    corrected = str(candidate.get("corrected_text", "")).strip()
    if corrected:
        return corrected
    return str(candidate.get("extracted_name", "")).strip()


def _normalize_thresholds(raw_thresholds: Any) -> dict[str, Any]:
    thresholds = raw_thresholds if isinstance(raw_thresholds, dict) else {}

    similarity = _clamp_int(
        thresholds.get("similarity_threshold", DEFAULT_SIMILARITY_THRESHOLD),
        minimum=50,
        maximum=100,
        fallback=DEFAULT_SIMILARITY_THRESHOLD,
    )
    recommendation = _clamp_int(
        thresholds.get("recommendation_threshold", DEFAULT_RECOMMENDATION_THRESHOLD),
        minimum=0,
        maximum=100,
        fallback=DEFAULT_RECOMMENDATION_THRESHOLD,
    )

    raw_temporal = thresholds.get("temporal_window_seconds", DEFAULT_TEMPORAL_WINDOW_SECONDS)
    try:
        temporal_window_seconds = float(raw_temporal)
    except (TypeError, ValueError):
        temporal_window_seconds = DEFAULT_TEMPORAL_WINDOW_SECONDS
    if temporal_window_seconds <= 0:
        temporal_window_seconds = DEFAULT_TEMPORAL_WINDOW_SECONDS

    return {
        "similarity_threshold": similarity,
        "recommendation_threshold": recommendation,
        "temporal_window_seconds": temporal_window_seconds,
    }


def _clamp_int(raw: Any, *, minimum: int, maximum: int, fallback: int) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return fallback
    return max(minimum, min(maximum, value))
