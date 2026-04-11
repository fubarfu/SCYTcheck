from __future__ import annotations

from src.data.models import LogRecord
from src.services.logging import LOG_HEADERS, write_sidecar_log


def test_fr049_sidecar_log_uses_fixed_expanded_schema(tmp_path) -> None:
    output = write_sidecar_log(
        str(tmp_path),
        "summary.csv",
        [
            LogRecord(
                timestamp_sec="00:00:01.234",
                raw_string="Player: Alice",
                accepted=True,
                rejection_reason="",
                extracted_name="Alice",
                region_id="region-1",
                matched_pattern="pattern-1",
                normalized_name="alice",
                occurrence_count=1,
                start_timestamp="00:00:01.234",
                end_timestamp="00:00:03.000",
                representative_region="10:20:100:50",
            )
        ],
    )

    lines = output.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(LOG_HEADERS)
    assert (
        lines[1]
        == (
            "00:00:01.234,Player: Alice,true,,Alice,region-1,pattern-1,"
            "alice,1,00:00:01.234,00:00:03.000,10:20:100:50"
        )
    )
