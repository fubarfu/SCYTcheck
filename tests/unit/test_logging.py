from __future__ import annotations

from src.services.logging import create_gating_log_record, should_write_detailed_sidecar


def test_should_write_detailed_sidecar_flag() -> None:
    assert should_write_detailed_sidecar(True) is True
    assert should_write_detailed_sidecar(False) is False


def test_create_gating_log_record_includes_required_fields() -> None:
    record = create_gating_log_record(
        frame_index=7,
        timestamp_sec="00:00:07.000",
        region_id="10:20:100:50",
        pixel_diff_value=0.015625,
        decision_action="skip_ocr",
        reason="diff_below_threshold",
    )

    assert record.timestamp_sec == "00:00:07.000"
    assert record.region_id == "10:20:100:50"
    assert record.raw_string == ""
    assert (
        record.tested_string_raw
        == "gating_frame_index=7; pixel_diff_value=0.015625"
    )
    assert record.tested_string_normalized == "gating_decision=skip_ocr"
    assert record.rejection_reason == "gating_diff_below_threshold"
    assert record.accepted is False
