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
class NormalizedOCRLine:
    """Represents OCR line content before and after normalization."""

    raw_lines: list[str] = field(default_factory=list)
    normalized_text: str = ""


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
class GatingStats:
    """Aggregate counters for frame-region gating behavior."""

    total_frame_region_pairs: int = 0
    ocr_executed_count: int = 0
    ocr_skipped_count: int = 0
    gating_enabled: bool = True
    gating_threshold: float = 0.02

    @property
    def skip_percentage(self) -> float:
        if self.total_frame_region_pairs <= 0:
            return 0.0
        return (self.ocr_skipped_count / self.total_frame_region_pairs) * 100.0


@dataclass
class TimingBreakdown:
    """Per-stage elapsed times for one analysis run, in milliseconds."""

    decode_ms: float = 0.0
    gating_ms: float = 0.0
    ocr_ms: float = 0.0
    post_processing_ms: float = 0.0
    total_ms: float = 0.0


@dataclass
class AnalysisRuntimeMetrics:
    """Runtime instrumentation metadata for one analysis execution."""

    timing_breakdown: TimingBreakdown | None = None
    instrumentation_enabled: bool = False
    instrumentation_overhead_pct: float = 0.0


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
    gating_stats: GatingStats | None = None
    runtime_metrics: AnalysisRuntimeMetrics | None = None
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


@dataclass
class PersistedAnalysisContext:
    """Restorable analysis context snapshot for history reopen."""

    context_id: str
    history_id: str
    scan_region: dict[str, int]
    output_folder: str
    context_patterns: list[dict[str, object]]
    analysis_settings: dict[str, object]
    saved_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AnalysisRunRecord:
    """One completed analysis run associated with a history entry."""

    run_id: str
    history_id: str
    completed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    result_csv_path: str = ""
    sidecar_review_path: str | None = None
    frame_count_processed: int | None = None
    settings_snapshot_id: str = ""


@dataclass
class VideoHistoryEntry:
    """Persistent canonical entry representing one analyzed video identity."""

    history_id: str
    canonical_source: str
    source_type: str
    display_name: str
    output_folder: str
    duration_seconds: int | None = None
    merge_key: str | None = None
    potential_duplicate: bool = False
    last_result_csv: str | None = None
    run_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted: bool = False
    runs: list[AnalysisRunRecord] = field(default_factory=list)
    contexts: list[PersistedAnalysisContext] = field(default_factory=list)


@dataclass
class DerivedReviewResultSet:
    """Derived review artifacts discovered from persisted output folder."""

    history_id: str
    resolved_csv_paths: list[str]
    resolution_status: str
    resolution_messages: list[str]
    resolved_sidecar_paths: list[str] = field(default_factory=list)
    primary_csv_path: str | None = None
    resolved_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ReviewGroupSessionState:
    """Persisted review-group controls and resolution state per group."""

    accepted_names: dict[str, str] = field(default_factory=dict)
    rejected_candidates: dict[str, list[str]] = field(default_factory=dict)
    collapsed_groups: dict[str, bool] = field(default_factory=dict)
    resolution_status: dict[str, str] = field(default_factory=dict)


@dataclass
class ReviewGroupCandidate:
    """Typed view of one candidate in a review group payload."""

    candidate_id: str
    extracted_name: str
    corrected_text: str = ""
    status: str = "pending"

    @property
    def display_name(self) -> str:
        text = (self.corrected_text or "").strip()
        if text:
            return text
        return self.extracted_name.strip()


@dataclass
class ReviewGroupPayload:
    """Typed representation of one API review group."""

    group_id: str
    accepted_name: str | None = None
    rejected_candidate_ids: list[str] = field(default_factory=list)
    is_collapsed: bool = False
    resolution_status: str = "UNRESOLVED"
    candidates: list[ReviewGroupCandidate] = field(default_factory=list)

    @property
    def active_spellings(self) -> set[str]:
        rejected = set(self.rejected_candidate_ids)
        values = {
            candidate.display_name
            for candidate in self.candidates
            if candidate.candidate_id not in rejected and candidate.display_name
        }
        return values
