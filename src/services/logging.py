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
