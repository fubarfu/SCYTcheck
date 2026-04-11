from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Region:
    """Represents a rectangular region in a video frame with temporal context."""

    x: int
    y: int
    width: int
    height: int
    frame_time: float = 0.0  # Time in seconds when region was selected

    @property
    def as_tuple(self) -> tuple[int, int, int, int]:
        """Return region as (x, y, width, height) tuple for backwards compatibility."""
        return (self.x, self.y, self.width, self.height)


@dataclass
class ContextPattern:
    """User-defined rule for extracting names from OCR lines."""

    id: str
    before_text: str | None = None
    after_text: str | None = None
    enabled: bool = True
    similarity_threshold: float = 0.75


@dataclass
class TextDetection:
    """Per-frame candidate extracted from OCR output."""

    raw_ocr_text: str
    extracted_name: str
    normalized_name: str
    region_id: str
    frame_time_sec: float
    matched_pattern_id: str | None = None


@dataclass
class AppearanceEvent:
    """One merged on-screen appearance interval for a normalized name."""

    normalized_name: str
    display_name: str
    start_time_sec: float
    end_time_sec: float
    region_ids: set[str] = field(default_factory=set)


@dataclass
class PlayerSummary:
    """Deduplicated output row for export."""

    player_name: str
    start_timestamp: str
    normalized_name: str = ""
    occurrence_count: int = 0
    first_seen_sec: float = 0.0
    last_seen_sec: float = 0.0
    representative_region: str = ""


@dataclass
class LogRecord:
    timestamp_sec: str
    raw_string: str
    tested_string_raw: str
    tested_string_normalized: str
    accepted: bool
    rejection_reason: str
    extracted_name: str
    region_id: str
    matched_pattern: str
    normalized_name: str
    occurrence_count: int
    start_timestamp: str
    end_timestamp: str
    representative_region: str


@dataclass
class TextString:
    content: str
    x: int
    y: int
    width: int
    height: int
    frequency: int = 1
    frame_time: float = 0.0  # Time in seconds when text was detected

    @property
    def region(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)


@dataclass
class VideoAnalysis:
    url: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    regions: list[Region] = field(default_factory=list)
    context_patterns: list[ContextPattern] = field(default_factory=list)
    filter_non_matching: bool = False
    video_quality: str = "best"
    logging_enabled: bool = False
    event_gap_threshold_sec: float = 1.0
    detections: list[TextDetection] = field(default_factory=list)
    log_records: list[LogRecord] = field(default_factory=list)
    player_summaries: list[PlayerSummary] = field(default_factory=list)
    text_strings: list[TextString] = field(default_factory=list)
    _index: dict[tuple[str, int, int, int, int], TextString] = field(
        default_factory=dict,
        init=False,
    )

    def add_detection(
        self, content: str, region: tuple[int, int, int, int], frame_time: float = 0.0
    ) -> None:
        cleaned = content.strip()
        if not cleaned:
            return

        x, y, width, height = region
        key = (cleaned.lower(), x, y, width, height)
        existing = self._index.get(key)
        if existing:
            existing.frequency += 1
            return

        text_string = TextString(
            content=cleaned,
            x=x,
            y=y,
            width=width,
            height=height,
            frequency=1,
            frame_time=frame_time,
        )
        self.text_strings.append(text_string)
        self._index[key] = text_string

    def add_detection_record(self, detection: TextDetection) -> None:
        """Store one extracted per-frame detection record."""
        self.detections.append(detection)

    def add_log_record(self, record: LogRecord) -> None:
        self.log_records.append(record)

    def set_player_summaries(self, summaries: Iterable[PlayerSummary]) -> None:
        """Replace deduplicated summaries with latest aggregation output."""
        self.player_summaries = list(summaries)
