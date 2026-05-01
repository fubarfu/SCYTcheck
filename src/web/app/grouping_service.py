from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher


_TEMPORAL_RELAXATION_MAX = 25.0
_MIN_SIMILARITY_FLOOR = 40.0


@dataclass
class GroupingThresholds:
    similarity_threshold: int = 85
    temporal_window_seconds: float = 2.0
    spelling_influence: int = 100
    temporal_influence: int = 60


def _name_similarity(a: str, b: str) -> float:
    a_norm = _normalize_for_similarity(a)
    b_norm = _normalize_for_similarity(b)
    if not a_norm or not b_norm:
        return 0.0
    overlap = len(set(a_norm) & set(b_norm))
    union = len(set(a_norm) | set(b_norm))
    jaccard_score = (overlap / union) * 100.0 if union else 0.0
    sequence_score = SequenceMatcher(None, a_norm, b_norm).ratio() * 100.0
    # Blend set-overlap and positional similarity to reduce OCR noise sensitivity
    # without making strict thresholds overly permissive.
    return (jaccard_score * 0.6) + (sequence_score * 0.4)


def _normalize_for_similarity(value: str) -> str:
    text = str(value or "").strip().lower()
    # Ignore punctuation/noise so OCR variants compare on meaningful characters.
    return re.sub(r"[^a-z0-9]", "", text)


class GroupingService:
    @staticmethod
    def build_groups(candidates: list[dict], thresholds: GroupingThresholds) -> list[dict]:
        groups: list[dict] = []
        for candidate in candidates:
            name = str(candidate.get("corrected_text") or candidate.get("extracted_name") or "")
            ts = _parse_timestamp_seconds(candidate.get("start_timestamp"))
            assigned = False
            for group in groups:
                best_similarity, time_distance = _group_match_stats(name, ts, group)
                temporal_proximity = max(0.0, 100.0 - time_distance * 20.0)
                required_similarity = _required_similarity(
                    thresholds.similarity_threshold,
                    thresholds.temporal_window_seconds,
                    thresholds.spelling_influence,
                    thresholds.temporal_influence,
                    time_distance,
                )
                if best_similarity >= required_similarity:
                    enriched = dict(candidate)
                    enriched["temporal_proximity"] = round(temporal_proximity, 1)
                    group["candidates"].append(enriched)
                    assigned = True
                    break
            if not assigned:
                enriched = dict(candidate)
                enriched["temporal_proximity"] = 100.0
                groups.append(
                    {
                        "group_id": f"grp_{len(groups) + 1}",
                        "display_name": name,
                        "anchor_timestamp": ts,
                        "candidates": [enriched],
                    }
                )
        return groups


def _group_match_stats(candidate_name: str, candidate_ts: float, group: dict) -> tuple[float, float]:
    group_candidates = list(group.get("candidates", []))
    if not group_candidates:
        ref_name = str(group.get("display_name", ""))
        ref_ts = float(group.get("anchor_timestamp", candidate_ts))
        return _name_similarity(candidate_name, ref_name), abs(candidate_ts - ref_ts)

    best_similarity = 0.0
    min_time_distance: float | None = None
    for member in group_candidates:
        member_name = str(member.get("corrected_text") or member.get("extracted_name") or "")
        member_ts = _parse_timestamp_seconds(member.get("start_timestamp"))
        similarity = _name_similarity(candidate_name, member_name)
        if similarity > best_similarity:
            best_similarity = similarity
        time_distance = abs(candidate_ts - member_ts)
        if min_time_distance is None or time_distance < min_time_distance:
            min_time_distance = time_distance

    return best_similarity, float(min_time_distance if min_time_distance is not None else 0.0)


def _required_similarity(
    similarity_threshold: int,
    temporal_window_seconds: float,
    spelling_influence: int,
    temporal_influence: int,
    time_distance_seconds: float,
) -> float:
    """Return required similarity using spelling strictness plus temporal boost.

    Temporal proximity is suggestive (not mandatory): close timestamps may relax
    the required similarity, but a spelling floor always remains.
    """
    influence_ratio = max(0.0, min(1.0, float(spelling_influence) / 100.0))
    # Use a non-linear curve so mid-range spelling influence is clearly
    # more permissive while 100 remains strict.
    effective_spelling_weight = influence_ratio ** 2.0
    base = _MIN_SIMILARITY_FLOOR + (
        (float(similarity_threshold) - _MIN_SIMILARITY_FLOOR) * effective_spelling_weight
    )

    if temporal_window_seconds <= 0:
        return max(_MIN_SIMILARITY_FLOOR, base)

    if time_distance_seconds > temporal_window_seconds:
        return max(_MIN_SIMILARITY_FLOOR, base)

    temporal_ratio = max(0.0, min(1.0, float(temporal_influence) / 100.0))
    max_relaxation = _TEMPORAL_RELAXATION_MAX * temporal_ratio
    closeness = 1.0 - (time_distance_seconds / temporal_window_seconds)
    closeness = max(0.0, min(1.0, closeness))
    relaxed = base - (max_relaxation * closeness)
    return max(_MIN_SIMILARITY_FLOOR, relaxed)


def _parse_timestamp_seconds(raw: object) -> float:
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
