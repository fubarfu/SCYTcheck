from __future__ import annotations

from tests.integration.test_us3_logging_throughput import (
    test_us3_logging_disabled_throughput_is_at_least_15_percent_higher,
)


def test_sc005_logging_off_throughput_target() -> None:
    test_us3_logging_disabled_throughput_is_at_least_15_percent_higher()
