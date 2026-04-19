from __future__ import annotations

from tests.integration.test_us3_gating_performance import (
    test_us3_gating_enabled_is_at_least_30_percent_faster_on_static_frames,
)


def test_sc003_runtime_reduction_target() -> None:
    test_us3_gating_enabled_is_at_least_30_percent_faster_on_static_frames()
