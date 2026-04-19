from __future__ import annotations

import csv
import logging
from pathlib import Path

from src.data.models import LogRecord


def configure_logging(log_level: str = "INFO", log_file: str | None = None) -> logging.Logger:
    logger = logging.getLogger("scytcheck")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def should_write_detailed_sidecar(logging_enabled: bool) -> bool:
    """Return whether detailed sidecar records should be generated for this run."""
    return bool(logging_enabled)


def create_gating_log_record(
    *,
    frame_index: int,
    timestamp_sec: str,
    region_id: str,
    pixel_diff_value: float,
    decision_action: str,
    reason: str,
) -> LogRecord:
    """Build one detailed gating sidecar record using the existing log schema."""
    rejection_reason = reason if reason.startswith("gating_") else f"gating_{reason}"
    return LogRecord(
        timestamp_sec=timestamp_sec,
        raw_string="",
        tested_string_raw=(
            f"gating_frame_index={frame_index}; pixel_diff_value={pixel_diff_value:.6f}"
        ),
        tested_string_normalized=f"gating_decision={decision_action}",
        accepted=False,
        rejection_reason=rejection_reason,
        extracted_name="",
        region_id=region_id,
        matched_pattern="",
        normalized_name="",
        occurrence_count=0,
        start_timestamp="",
        end_timestamp="",
        representative_region="",
    )


LOG_HEADERS = [
    "TimestampSec",
    "RawString",
    "TestedStringRaw",
    "TestedStringNormalized",
    "Accepted",
    "RejectionReason",
    "ExtractedName",
    "RegionId",
    "MatchedPattern",
    "NormalizedName",
    "OccurrenceCount",
    "StartTimestamp",
    "EndTimestamp",
    "RepresentativeRegion",
]


class SidecarLogWriter:
    """
    Context manager for streaming sidecar log writes during analysis.
    Each LogRecord is written and flushed to disk immediately upon generation.
    """

    def __init__(self, output_folder: str, summary_filename: str) -> None:
        """
        Initialize the writer with output location.

        Args:
            output_folder: Directory where the log file will be written
            summary_filename: Summary CSV filename; used to derive the sidecar log name
        """
        self._folder = Path(output_folder)
        self._path = self._folder / sidecar_log_name(summary_filename)
        self._handle: object = None  # Will be opened in __enter__
        self._writer: csv.writer | None = None

    def __enter__(self) -> SidecarLogWriter:
        """
        Open the log file and write the header row.

        Returns:
            self

        Raises:
            OSError: If file cannot be created or written
        """
        self._folder.mkdir(parents=True, exist_ok=True)
        # type: ignore - csv module doesn't have full type stubs
        self._handle = open(  # type: ignore[assignment]
            self._path, "w", newline="", encoding="utf-8"
        )
        self._writer = csv.writer(self._handle)  # type: ignore[arg-type]
        self._writer.writerow(LOG_HEADERS)
        self._handle.flush()  # type: ignore[union-attr]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """
        Close the log file handle unconditionally.

        Closure happens even if exc_type is not None (exception in context).
        Exceptions are not suppressed.
        """
        if self._handle is not None:
            self._handle.close()  # type: ignore[union-attr]
        self._handle = None
        self._writer = None

    def write_record(self, record: LogRecord) -> None:
        """
        Write one LogRecord as a CSV row and flush.

        Failures are non-fatal: OSError is caught and logged as a warning.
        Analysis continues even if a write fails.

        Args:
            record: LogRecord to write
        """
        if self._writer is None:
            return

        logger = logging.getLogger("scytcheck")
        try:
            self._writer.writerow(
                [
                    record.timestamp_sec,
                    record.raw_string,
                    record.tested_string_raw,
                    record.tested_string_normalized,
                    str(record.accepted).lower(),
                    record.rejection_reason,
                    record.extracted_name,
                    record.region_id,
                    record.matched_pattern,
                    record.normalized_name,
                    record.occurrence_count,
                    record.start_timestamp,
                    record.end_timestamp,
                    record.representative_region,
                ]
            )
            self._handle.flush()  # type: ignore[union-attr]
        except OSError as e:
            logger.warning(f"Failed to write sidecar log record: {e}")


def sidecar_log_name(summary_filename: str) -> str:
    path = Path(summary_filename)
    return f"{path.stem}_log.csv"


def write_sidecar_log(output_folder: str, summary_filename: str, records: list[LogRecord]) -> Path:
    folder = Path(output_folder)
    folder.mkdir(parents=True, exist_ok=True)
    output_path = folder / sidecar_log_name(summary_filename)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(LOG_HEADERS)
        for record in records:
            writer.writerow(
                [
                    record.timestamp_sec,
                    record.raw_string,
                    record.tested_string_raw,
                    record.tested_string_normalized,
                    str(record.accepted).lower(),
                    record.rejection_reason,
                    record.extracted_name,
                    record.region_id,
                    record.matched_pattern,
                    record.normalized_name,
                    record.occurrence_count,
                    record.start_timestamp,
                    record.end_timestamp,
                    record.representative_region,
                ]
            )

    return output_path
