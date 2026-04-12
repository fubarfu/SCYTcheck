from __future__ import annotations

from tests.integration.helpers.memory_helpers import checkpoint_indices, percent_delta


def test_memory_checkpoint_indices_for_two_hour_iteration() -> None:
    start_idx, middle_idx, end_idx = checkpoint_indices(7200)
    assert start_idx == 0
    assert middle_idx == 3600
    assert end_idx == 7199


def test_memory_rss_variance_stays_within_ten_percent_budget() -> None:
    rss_checkpoints_mb = [200.0, 214.0, 208.0]
    deltas = [abs(percent_delta(rss_checkpoints_mb[0], value)) for value in rss_checkpoints_mb[1:]]
    assert max(deltas) <= 10.0
