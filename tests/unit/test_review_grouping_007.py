from __future__ import annotations

from src.web.app.grouping_service import GroupingService, GroupingThresholds


def test_grouping_clusters_similar_names_with_temporal_proximity() -> None:
    candidates = [
        {"candidate_id": "c1", "extracted_name": "Alice", "start_timestamp": 1.0},
        {"candidate_id": "c2", "extracted_name": "Alicee", "start_timestamp": 1.6},
        {"candidate_id": "c3", "extracted_name": "Bob", "start_timestamp": 20.0},
    ]
    groups = GroupingService.build_groups(
        candidates, GroupingThresholds(similarity_threshold=60, temporal_window_seconds=3.0)
    )
    assert len(groups) == 2
    first_group_candidates = groups[0]["candidates"]
    assert len(first_group_candidates) == 2
    assert "temporal_proximity" in first_group_candidates[0]


def test_grouping_recompute_changes_group_count_when_threshold_changes() -> None:
    candidates = [
        {"candidate_id": "c1", "extracted_name": "Alpha", "start_timestamp": 1.0},
        {"candidate_id": "c2", "extracted_name": "Alphx", "start_timestamp": 1.2},
    ]
    strict = GroupingService.build_groups(candidates, GroupingThresholds(similarity_threshold=95))
    loose = GroupingService.build_groups(candidates, GroupingThresholds(similarity_threshold=50))
    assert len(strict) >= len(loose)


def test_grouping_accepts_clock_format_timestamps() -> None:
    candidates = [
        {"candidate_id": "c1", "extracted_name": "Grynal", "start_timestamp": "00:00:04.000"},
        {"candidate_id": "c2", "extracted_name": "Grynal", "start_timestamp": "00:00:05.000"},
    ]

    groups = GroupingService.build_groups(
        candidates,
        GroupingThresholds(similarity_threshold=70, temporal_window_seconds=3.0),
    )

    assert len(groups) == 1
    assert len(groups[0]["candidates"]) == 2
