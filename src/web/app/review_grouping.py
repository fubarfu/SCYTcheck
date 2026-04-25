from __future__ import annotations

from typing import Any

from src.web.app.grouping_service import GroupingService, GroupingThresholds
from src.web.app.recommendation_service import RecommendationService

DEFAULT_SIMILARITY_THRESHOLD = 80
DEFAULT_RECOMMENDATION_THRESHOLD = 70
DEFAULT_TEMPORAL_WINDOW_SECONDS = 2.0


def recompute_groups(session_payload: dict[str, Any]) -> dict[str, Any]:
    """Recompute review groups and recommendation metadata from current candidates."""
    payload = dict(session_payload or {})
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

    payload["thresholds"] = thresholds
    payload["groups"] = scored_groups
    return payload


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
