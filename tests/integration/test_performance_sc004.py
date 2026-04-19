from __future__ import annotations

from tests.integration.test_us3_gating_accuracy import (
    test_us3_gated_and_ungated_detection_variance_is_within_one_percent,
)


def test_sc004_detection_variance_target() -> None:
    test_us3_gated_and_ungated_detection_variance_is_within_one_percent()
