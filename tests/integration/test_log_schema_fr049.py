from __future__ import annotations

import numpy as np

from src.data.models import LogRecord
from src.services.analysis_service import AnalysisService
from src.services.logging import LOG_HEADERS, SidecarLogWriter, write_sidecar_log


def test_fr049_sidecar_log_uses_fixed_expanded_schema(tmp_path) -> None:
    output = write_sidecar_log(
        str(tmp_path),
        "summary.csv",
        [
            LogRecord(
                timestamp_sec="00:00:01.234",
                raw_string="Player: Alice",
                tested_string_raw="Player: Alice",
                tested_string_normalized="Player: Alice",
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
            "00:00:01.234,Player: Alice,Player: Alice,Player: Alice,true,,Alice,region-1,pattern-1,"
            "alice,1,00:00:01.234,00:00:03.000,10:20:100:50"
        )
    )


def test_sidecar_log_streaming_preserves_entries_on_interruption(tmp_path) -> None:
    """
    Test that streaming writes preserve all entries if analysis is interrupted (T012 - US2).

    Simulates writing 3 log records then "interrupting" (exiting context early).
    Verifies log file contains all 3 entries plus header.
    """
    writer = SidecarLogWriter(str(tmp_path), "test_streaming.csv")
    writer.__enter__()

    records = [
        LogRecord(
            timestamp_sec="00:00:01.000",
            raw_string="Frame1",
            tested_string_raw="Frame1",
            tested_string_normalized="frame1",
            accepted=True,
            rejection_reason="",
            extracted_name="Frame1",
            region_id="r1",
            matched_pattern="p1",
            normalized_name="frame1",
            occurrence_count=1,
            start_timestamp="00:00:01.000",
            end_timestamp="00:00:02.000",
            representative_region="0:0:100:100",
        ),
        LogRecord(
            timestamp_sec="00:00:02.000",
            raw_string="Frame2",
            tested_string_raw="Frame2",
            tested_string_normalized="frame2",
            accepted=True,
            rejection_reason="",
            extracted_name="Frame2",
            region_id="r1",
            matched_pattern="p1",
            normalized_name="frame2",
            occurrence_count=1,
            start_timestamp="00:00:02.000",
            end_timestamp="00:00:03.000",
            representative_region="0:0:100:100",
        ),
        LogRecord(
            timestamp_sec="00:00:03.000",
            raw_string="Frame3",
            tested_string_raw="Frame3",
            tested_string_normalized="frame3",
            accepted=True,
            rejection_reason="",
            extracted_name="Frame3",
            region_id="r1",
            matched_pattern="p1",
            normalized_name="frame3",
            occurrence_count=1,
            start_timestamp="00:00:03.000",
            end_timestamp="00:00:04.000",
            representative_region="0:0:100:100",
        ),
    ]

    # Write all 3 records
    for record in records:
        writer.write_record(record)

    # Simulate interruption by exiting the context
    writer.__exit__(None, None, None)

    # Verify file contains header + 3 data rows (no data loss on interruption)
    content = writer._path.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    assert len(lines) == 4  # header + 3 data rows
    assert lines[0] == ",".join(LOG_HEADERS)
    assert "Frame1" in lines[1]
    assert "Frame2" in lines[2]
    assert "Frame3" in lines[3]


def test_timing_emission_only_when_logging_enabled() -> None:
    class VideoServiceStub:
        @staticmethod
        def iterate_frames_with_timestamps(url, start_time, end_time, fps, quality="best"):
            frame = np.zeros((32, 32, 3), dtype=np.uint8)
            yield (0.0, frame)
            yield (0.5, frame)

    class OCRServiceStub:
        @staticmethod
        def detect_text(frame, region):
            return ["PLAYER 1"]

        @staticmethod
        def extract_candidates(tokens, patterns=None, filter_non_matching=False, tolerance_threshold=0.75):
            return []

    service = AnalysisService(VideoServiceStub(), OCRServiceStub())
    regions = [(0, 0, 16, 16)]

    disabled = service.analyze(
        url="mock://video",
        regions=regions,
        start_time=0.0,
        end_time=1.0,
        fps=2,
        logging_enabled=False,
    )
    assert disabled.runtime_metrics is None

    enabled = service.analyze(
        url="mock://video",
        regions=regions,
        start_time=0.0,
        end_time=1.0,
        fps=2,
        logging_enabled=True,
    )
    assert enabled.runtime_metrics is not None
    assert enabled.runtime_metrics.instrumentation_enabled is True
    assert enabled.runtime_metrics.timing_breakdown is not None
    assert enabled.runtime_metrics.timing_breakdown.total_ms >= 0.0
