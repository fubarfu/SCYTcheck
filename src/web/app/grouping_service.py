from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GroupingThresholds:
    similarity_threshold: int = 85
    temporal_window_seconds: float = 2.0


def _name_similarity(a: str, b: str) -> float:
    a_norm = a.strip().lower()
    b_norm = b.strip().lower()
    if not a_norm or not b_norm:
        return 0.0
    overlap = len(set(a_norm) & set(b_norm))
    union = len(set(a_norm) | set(b_norm))
    return (overlap / union) * 100.0 if union else 0.0


class GroupingService:
    @staticmethod
    def build_groups(candidates: list[dict], thresholds: GroupingThresholds) -> list[dict]:
        groups: list[dict] = []
        for candidate in candidates:
            name = str(candidate.get("corrected_text") or candidate.get("extracted_name") or "")
            ts = _parse_timestamp_seconds(candidate.get("start_timestamp"))
            assigned = False
            for group in groups:
                ref_name = str(group["display_name"])
                ref_ts = float(group.get("anchor_timestamp", ts))
                sim = _name_similarity(name, ref_name)
                temporal_proximity = max(0.0, 100.0 - abs(ts - ref_ts) * 20.0)
                if (
                    sim >= thresholds.similarity_threshold
                    and abs(ts - ref_ts) <= thresholds.temporal_window_seconds
                ):
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
