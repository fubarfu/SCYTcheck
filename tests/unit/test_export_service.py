from datetime import datetime
from pathlib import Path

import pytest

from src.data.models import ContextPattern, GatingStats, PlayerSummary, VideoAnalysis
from src.services.export_service import ExportService


def test_export_to_csv_writes_header_only_when_no_summaries(tmp_path: Path) -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=abc")

    service = ExportService()
    exported = service.export_to_csv(analysis, str(tmp_path), "output.csv")

    assert exported.exists()
    content = exported.read_text(encoding="utf-8")
    assert content.strip() == "PlayerName,StartTimestamp"


def test_extract_youtube_video_id() -> None:
    """Test video ID extraction from various YouTube URL formats."""
    service = ExportService()

    # Standard youtube.com URL
    assert (
        service.extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        == "dQw4w9WgXcQ"
    )

    # youtube.com URL with additional parameters
    assert (
        service.extract_youtube_video_id("https://youtube.com/watch?v=abc123&t=10s&list=xyz")
        == "abc123"
    )

    # youtu.be short URL
    assert service.extract_youtube_video_id("https://youtu.be/shorturl123") == "shorturl123"

    # youtu.be with query parameters
    assert service.extract_youtube_video_id("https://youtu.be/vid456?t=5") == "vid456"


def test_extract_youtube_video_id_invalid() -> None:
    """Test that invalid URLs raise ValueError."""
    service = ExportService()

    with pytest.raises(ValueError):
        service.extract_youtube_video_id("https://example.com/video")

    with pytest.raises(ValueError):
        service.extract_youtube_video_id("https://youtube.com/channel/UCxyz")


def test_generate_filename() -> None:
    """Test auto-filename generation with various inputs."""
    service = ExportService()
    test_time = datetime(2026, 4, 11, 14, 30, 45)

    # Basic youtube.com URL
    filename = service.generate_filename("https://youtube.com/watch?v=test123", test_time)
    assert filename == "scytcheck_test123_20260411-143045.csv"

    # youtu.be short URL
    filename = service.generate_filename("https://youtu.be/vid456", test_time)
    assert filename == "scytcheck_vid456_20260411-143045.csv"

    # URL with query parameters
    filename = service.generate_filename(
        "https://youtube.com/watch?v=abc&t=10s&list=xyz", test_time
    )
    assert filename == "scytcheck_abc_20260411-143045.csv"


def test_generate_filename_uses_current_time_when_not_specified() -> None:
    """Test that generate_filename uses current time by default."""
    service = ExportService()

    filename = service.generate_filename("https://youtube.com/watch?v=testid")

    # Should contain video ID and timestamp format
    assert "scytcheck_testid_" in filename
    assert filename.endswith(".csv")

    # Check timestamp format YYYYMMDD-HHMMSS
    parts = filename.replace("scytcheck_", "").replace(".csv", "").split("_")
    timestamp_part = parts[-1]
    assert len(timestamp_part) == 15  # YYYYMMDD-HHMMSS
    assert timestamp_part[8] == "-"


def test_export_player_summary_schema_order(tmp_path: Path) -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=abc")
    analysis.set_player_summaries(
        [
            PlayerSummary(
                player_name="Alice",
                start_timestamp="00:00:01.000",
                normalized_name="alice",
                occurrence_count=3,
                first_seen_sec=1.0,
                last_seen_sec=9.5,
                representative_region="r1",
            )
        ]
    )

    service = ExportService()
    exported = service.export_to_csv(analysis, str(tmp_path), "summary.csv")
    lines = exported.read_text(encoding="utf-8").splitlines()

    assert lines[0] == "PlayerName,StartTimestamp"
    assert lines[1] == "Alice,00:00:01.000"


def test_export_to_csv_writes_header_only_summary_when_no_text_detected(tmp_path: Path) -> None:
    analysis = VideoAnalysis(
        url="https://youtube.com/watch?v=abc",
        context_patterns=[ContextPattern(id="joined", after_text="joined")],
    )

    service = ExportService()
    exported = service.export_to_csv(analysis, str(tmp_path), "empty-summary.csv")
    lines = exported.read_text(encoding="utf-8").splitlines()

    assert lines == ["PlayerName,StartTimestamp"]


def test_format_gating_summary_includes_counts_and_percentage() -> None:
    stats = GatingStats(total_frame_region_pairs=10, ocr_executed_count=7, ocr_skipped_count=3)

    summary = ExportService.format_gating_summary(stats)

    assert "Evaluated 10" in summary
    assert "OCR Executed 7" in summary
    assert "OCR Skipped 3" in summary
    assert "30.0%" in summary


# ============================================================================
# SidecarLogWriter Tests
# ============================================================================


def test_sidecar_log_writer_enter_creates_file_with_header(tmp_path: Path) -> None:
    """Test that __enter__ creates the file with header row only."""
    from src.services.logging import SidecarLogWriter

    writer = SidecarLogWriter(str(tmp_path), "test_output.csv")
    writer_ctx = writer.__enter__()

    assert writer_ctx is writer
    assert writer._path.exists()

    # Read the file and verify header-only content
    content = writer._path.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    assert len(lines) == 1
    assert "TimestampSec" in lines[0]
    assert "RawString" in lines[0]

    writer.__exit__(None, None, None)


def test_sidecar_log_writer_write_record_appends_row_and_flushes(tmp_path: Path) -> None:
    """Test that write_record appends one data row and the file is flushed."""
    from src.data.models import LogRecord
    from src.services.logging import SidecarLogWriter

    writer = SidecarLogWriter(str(tmp_path), "test_output.csv")
    writer.__enter__()

    record = LogRecord(
        timestamp_sec="00:00:01.000",
        raw_string="test_string",
        tested_string_raw="test_string",
        tested_string_normalized="test_string",
        accepted=True,
        rejection_reason="",
        extracted_name="test_name",
        region_id="0:0:100:100",
        matched_pattern="pattern1",
        normalized_name="test_name",
        occurrence_count=1,
        start_timestamp="00:00:01.000",
        end_timestamp="00:00:05.000",
        representative_region="0:0:100:100",
    )
    writer.write_record(record)

    # Verify file has header + 1 data row
    content = writer._path.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    assert len(lines) == 2
    assert "test_string" in lines[1]

    writer.__exit__(None, None, None)


def test_sidecar_log_writer_exit_closes_file(tmp_path: Path) -> None:
    """Test that __exit__ closes the file handle."""
    from src.services.logging import SidecarLogWriter

    writer = SidecarLogWriter(str(tmp_path), "test_output.csv")
    writer.__enter__()

    assert writer._handle is not None
    assert writer._writer is not None

    writer.__exit__(None, None, None)

    # After exit, handle and writer should be None
    assert writer._handle is None
    assert writer._writer is None

    # File should still exist (not deleted)
    assert writer._path.exists()


def test_sidecar_log_writer_flush_called_per_write_record(tmp_path: Path) -> None:
    """Test that flush() is called after each write_record invocation (T011 - US2)."""

    from src.data.models import LogRecord
    from src.services.logging import SidecarLogWriter

    writer = SidecarLogWriter(str(tmp_path), "test_output.csv")
    writer.__enter__()

    record = LogRecord(
        timestamp_sec="00:00:01.000",
        raw_string="test",
        tested_string_raw="test",
        tested_string_normalized="test",
        accepted=True,
        rejection_reason="",
        extracted_name="test",
        region_id="0:0:100:100",
        matched_pattern="",
        normalized_name="test",
        occurrence_count=1,
        start_timestamp="",
        end_timestamp="",
        representative_region="",
    )

    # Mock the flush method to track calls
    original_flush = writer._handle.flush
    flush_call_count = 0

    def mock_flush():
        nonlocal flush_call_count
        flush_call_count += 1
        original_flush()

    writer._handle.flush = mock_flush

    # Write a record
    writer.write_record(record)
    assert flush_call_count == 1

    # Write another record
    writer.write_record(record)
    assert flush_call_count == 2

    writer.__exit__(None, None, None)


def test_sidecar_log_writer_no_file_without_context_entry(tmp_path: Path) -> None:
    """Test that constructing SidecarLogWriter without entering context does not create file."""
    from src.services.logging import SidecarLogWriter

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Construct but do NOT enter context
    writer = SidecarLogWriter(str(output_dir), "test_no_entry.csv")

    # File should NOT be created
    assert not writer._path.exists()

    # Also verify handle and writer are still None
    assert writer._handle is None
    assert writer._writer is None


def test_sidecar_log_writer_oserror_is_swallowed(tmp_path: Path) -> None:
    """Test that OSError in write_record is caught and does not raise."""
    from unittest.mock import patch

    from src.data.models import LogRecord
    from src.services.logging import SidecarLogWriter

    writer = SidecarLogWriter(str(tmp_path), "test_output.csv")
    writer.__enter__()

    record = LogRecord(
        timestamp_sec="00:00:01.000",
        raw_string="test",
        tested_string_raw="test",
        tested_string_normalized="test",
        accepted=True,
        rejection_reason="",
        extracted_name="test",
        region_id="0:0:100:100",
        matched_pattern="",
        normalized_name="test",
        occurrence_count=1,
        start_timestamp="",
        end_timestamp="",
        representative_region="",
    )

    # Mock the flush method to raise OSError
    with patch.object(writer._handle, "flush", side_effect=OSError("Disk full")):
        # This should not raise; the error should be caught
        writer.write_record(record)

    writer.__exit__(None, None, None)


def test_sidecar_log_writer_exit_closes_on_exception(tmp_path: Path) -> None:
    """Test that __exit__ closes the file even when an exception occurs."""
    from src.services.logging import SidecarLogWriter

    writer = SidecarLogWriter(str(tmp_path), "test_output.csv")
    writer.__enter__()

    # Simulate an exception in the context
    exc_type, exc_val, exc_tb = ValueError, ValueError("test error"), None
    writer.__exit__(exc_type, exc_val, exc_tb)

    # After exit, handle and writer should be None
    assert writer._handle is None
    assert writer._writer is None

    # File should still exist
    assert writer._path.exists()
