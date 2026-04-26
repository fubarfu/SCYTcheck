from __future__ import annotations

from typing import Any

from src.web.app.grouping_service import GroupingService, GroupingThresholds
from src.web.app.recommendation_service import RecommendationService
from src.web.app.review_sidecar_store import ReviewSidecarStore

DEFAULT_SIMILARITY_THRESHOLD = 80
DEFAULT_RECOMMENDATION_THRESHOLD = 70
DEFAULT_TEMPORAL_WINDOW_SECONDS = 2.0
DEFAULT_SPELLING_INFLUENCE = 50
DEFAULT_TEMPORAL_INFLUENCE = 50


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
            spelling_influence=thresholds["spelling_influence"],
            temporal_influence=thresholds["temporal_influence"],
        ),
    )
    scored_groups = RecommendationService.score_groups(
        groups,
        recommendation_threshold=thresholds["recommendation_threshold"],
    )

    scored_groups = _apply_candidate_group_overrides(payload, scored_groups)

    groups = _hydrate_group_state(payload, scored_groups)

    payload["thresholds"] = thresholds
    payload["groups"] = groups
    return payload


def _hydrate_group_state(payload: dict[str, Any], groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    accepted_map = dict(payload.get("accepted_names", {}))
    rejected_map = dict(payload.get("rejected_candidates", {}))
    collapsed_map = dict(payload.get("collapsed_groups", {}))
    status_map = dict(payload.get("resolution_status", {}))

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

        explicit_status = str(status_map.get(group_id, "")).strip().upper()
        preserve_unresolved = explicit_status == "UNRESOLVED"

        accepted_name = str(accepted_map.get(group_id, "")).strip()
        if accepted_name and accepted_name not in active_spellings:
            accepted_name = ""
        if not accepted_name and len(active_spellings) == 1 and not preserve_unresolved:
            accepted_name = active_spellings[0]

        if accepted_name:
            resolution_status = "RESOLVED"
        elif preserve_unresolved:
            resolution_status = "UNRESOLVED"
        else:
            # Exact-match consensus is based on active candidates only.
            resolution_status = "RESOLVED" if len(active_spellings) == 1 and active_candidates else "UNRESOLVED"

        explicit_collapsed = collapsed_map.get(group_id)
        remembered_is_collapsed = bool(explicit_collapsed) if explicit_collapsed is not None else None
        is_collapsed = (
            remembered_is_collapsed
            if remembered_is_collapsed is not None
            else resolution_status == "RESOLVED"
        )
        has_conflicting_spellings = len(active_spellings) > 1

        normalized_accepted[group_id] = accepted_name if accepted_name else ""
        normalized_collapsed[group_id] = is_collapsed
        normalized_status[group_id] = resolution_status

        group["accepted_name"] = accepted_name or None
        group["rejected_candidate_ids"] = rejected_candidate_ids
        group["is_collapsed"] = is_collapsed
        group["remembered_is_collapsed"] = remembered_is_collapsed
        group["resolution_status"] = normalized_status[group_id]
        group["has_conflicting_spellings"] = has_conflicting_spellings
        group["conflict_spelling_count"] = len(active_spellings)
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


def _apply_candidate_group_overrides(
    payload: dict[str, Any],
    groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    overrides = dict(payload.get("candidate_group_overrides", {}))
    if not overrides:
        return groups

    base_groups_by_id: dict[str, dict[str, Any]] = {
        str(group.get("group_id", "")).strip(): group
        for group in groups
        if str(group.get("group_id", "")).strip()
    }
    group_order = [
        str(group.get("group_id", "")).strip()
        for group in groups
        if str(group.get("group_id", "")).strip()
    ]

    grouped_candidates: dict[str, list[dict[str, Any]]] = {}

    for group in groups:
        base_group_id = str(group.get("group_id", "")).strip()
        for candidate in list(group.get("candidates", [])):
            candidate_id = str(candidate.get("candidate_id", "")).strip()
            if not candidate_id:
                continue
            target_group_id = str(overrides.get(candidate_id, base_group_id)).strip() or base_group_id
            grouped_candidates.setdefault(target_group_id, []).append(candidate)
            if target_group_id not in group_order:
                group_order.append(target_group_id)

    rebuilt: list[dict[str, Any]] = []
    for group_id in group_order:
        candidates = grouped_candidates.get(group_id, [])
        if not candidates:
            continue

        base_group = base_groups_by_id.get(group_id)
        display_name = _candidate_name(candidates[0])
        anchor_timestamp = _parse_timestamp_seconds(candidates[0].get("start_timestamp"))
        if base_group is not None:
            display_name = str(base_group.get("display_name", display_name))
            anchor_timestamp = float(base_group.get("anchor_timestamp", anchor_timestamp))

        rebuilt.append(
            {
                "group_id": group_id,
                "display_name": display_name,
                "anchor_timestamp": anchor_timestamp,
                "candidates": candidates,
            }
        )

    payload["candidate_group_overrides"] = {
        candidate_id: group_id
        for candidate_id, group_id in overrides.items()
        if group_id in grouped_candidates
    }

    return rebuilt


def _parse_timestamp_seconds(raw: Any) -> float:
    if raw is None:
        return 0.0
    value = str(raw).strip()
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        pass
    if ":" not in value:
        return 0.0
    parts = value.split(":")
    total = 0.0
    for index, part in enumerate(parts):
        try:
            piece = float(part)
        except ValueError:
            return 0.0
        if piece < 0:
            return 0.0
        multiplier = 60 ** (len(parts) - index - 1)
        total += piece * multiplier
    return total


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
    spelling_influence = _clamp_int(
        thresholds.get("spelling_influence", DEFAULT_SPELLING_INFLUENCE),
        minimum=0,
        maximum=100,
        fallback=DEFAULT_SPELLING_INFLUENCE,
    )
    temporal_influence = _clamp_int(
        thresholds.get("temporal_influence", DEFAULT_TEMPORAL_INFLUENCE),
        minimum=0,
        maximum=100,
        fallback=DEFAULT_TEMPORAL_INFLUENCE,
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
        "spelling_influence": spelling_influence,
        "temporal_influence": temporal_influence,
    }


def _clamp_int(raw: Any, *, minimum: int, maximum: int, fallback: int) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return fallback
    return max(minimum, min(maximum, value))
