from src.data.models import ContextPattern, TextDetection
from src.services.analysis_service import AnalysisService


class _VideoServiceStub:
    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        del url, start_time, end_time, fps, quality
        yield 12.0, [[0]]


class _OCRServiceStub:
    def detect_text(self, frame, region):
        del frame, region
        return ["Raw OCR Name"]

    def extract_candidates(self, tokens, patterns=None, filter_non_matching=False):
        del patterns, filter_non_matching
        return [(str(tokens[0]), None)]

    def evaluate_lines(self, lines, patterns=None, filter_non_matching=False):
        del lines, patterns, filter_non_matching
        return [
            {
                "raw_string": "Raw OCR Name",
                "accepted": False,
                "rejection_reason": "no_pattern_match",
                "extracted_name": "",
                "matched_pattern": None,
            }
        ]


class _OCRServiceDiagnosticsStub:
    def detect_text(self, frame, region):
        del frame, region
        return []

    def detect_text_with_diagnostics(self, frame, region):
        del frame, region
        return [], [
            {
                "raw_string": "Alice",
                "accepted": False,
                "rejection_reason": "low_confidence",
                "extracted_name": "",
                "matched_pattern": None,
            }
        ]

    def evaluate_lines(self, lines, patterns=None, filter_non_matching=False):
        del lines, patterns, filter_non_matching
        return []


class _StreamingVideoServiceStub:
    def __init__(self) -> None:
        self.frames_yielded = 0

    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        del url, start_time, end_time, fps, quality
        for frame_time in (0.0, 1.0, 2.0):
            self.frames_yielded += 1
            yield frame_time, [[self.frames_yielded]]


def test_normalize_name_lower_trim_and_collapse_spaces() -> None:
    assert AnalysisService.normalize_name("  Player   One  ") == "player one"


def test_format_timestamp_hh_mm_ss_mmm() -> None:
    assert AnalysisService.format_timestamp(0) == "00:00:00.000"
    assert AnalysisService.format_timestamp(1.234) == "00:00:01.234"
    assert AnalysisService.format_timestamp(3661.009) == "01:01:01.009"


def test_merge_appearance_events_merges_within_gap() -> None:
    detections = [
        ("player one", 1.0, "r1"),
        ("player one", 1.6, "r1"),
        ("player one", 4.0, "r2"),
    ]

    events = AnalysisService.merge_appearance_events(detections, gap_threshold_sec=1.0)

    assert len(events) == 2
    assert events[0].start_time_sec == 1.0
    assert events[0].end_time_sec == 1.6
    assert events[1].start_time_sec == 4.0
    assert events[1].end_time_sec == 4.0


def test_merge_appearance_events_separates_names() -> None:
    detections = [
        ("alice", 1.0, "r1"),
        ("bob", 1.2, "r1"),
        ("alice", 1.7, "r2"),
    ]

    events = AnalysisService.merge_appearance_events(detections, gap_threshold_sec=1.0)

    # alice has one merged event (1.0-1.7), bob has one event
    assert len(events) == 2
    names = sorted([e.normalized_name for e in events])
    assert names == ["alice", "bob"]


def test_build_player_summaries_deduplicates_by_normalized_name() -> None:
    detections = [
        TextDetection(
            raw_ocr_text="Player: Alice",
            extracted_name="Alice",
            normalized_name="alice",
            region_id="r1",
            frame_time_sec=1.0,
        ),
        TextDetection(
            raw_ocr_text="PLAYER:  Alice ",
            extracted_name=" Alice ",
            normalized_name="alice",
            region_id="r1",
            frame_time_sec=1.4,
        ),
        TextDetection(
            raw_ocr_text="Player: ALICE",
            extracted_name="ALICE",
            normalized_name="alice",
            region_id="r2",
            frame_time_sec=4.0,
        ),
        TextDetection(
            raw_ocr_text="Player: Bob",
            extracted_name="Bob",
            normalized_name="bob",
            region_id="r1",
            frame_time_sec=2.0,
        ),
    ]

    summaries = AnalysisService.build_player_summaries(detections, gap_threshold_sec=1.0)

    assert len(summaries) == 2
    by_name = {summary.normalized_name: summary for summary in summaries}
    assert by_name["alice"].occurrence_count == 2
    assert by_name["alice"].first_seen_sec == 1.0
    assert by_name["alice"].last_seen_sec == 4.0
    assert by_name["bob"].occurrence_count == 1


def test_build_player_summaries_uses_gap_threshold() -> None:
    detections = [
        TextDetection(
            raw_ocr_text="Player: Alice",
            extracted_name="Alice",
            normalized_name="alice",
            region_id="r1",
            frame_time_sec=1.0,
        ),
        TextDetection(
            raw_ocr_text="Player: Alice",
            extracted_name="Alice",
            normalized_name="alice",
            region_id="r1",
            frame_time_sec=2.2,
        ),
    ]

    summaries = AnalysisService.build_player_summaries(detections, gap_threshold_sec=1.0)

    assert summaries[0].occurrence_count == 2


def test_analyze_records_rejected_ocr_rows_when_logging_enabled() -> None:
    service = AnalysisService(video_service=_VideoServiceStub(), ocr_service=_OCRServiceStub())

    analysis = service.analyze(
        url="https://youtube.com/watch?v=test",
        regions=[(10, 20, 100, 50)],
        start_time=0.0,
        end_time=60.0,
        fps=1,
        context_patterns=[ContextPattern(id="joined", after_text="joined")],
        filter_non_matching=True,
        logging_enabled=True,
    )

    assert analysis.player_summaries == []
    assert len(analysis.log_records) == 1
    row = analysis.log_records[0]
    assert row.accepted is False
    assert row.rejection_reason == "no_pattern_match"
    assert row.raw_string == "Raw OCR Name"


def test_analyze_records_low_confidence_rejection_when_logging_enabled() -> None:
    service = AnalysisService(
        video_service=_VideoServiceStub(), ocr_service=_OCRServiceDiagnosticsStub()
    )

    analysis = service.analyze(
        url="https://youtube.com/watch?v=test",
        regions=[(10, 20, 100, 50)],
        start_time=0.0,
        end_time=60.0,
        fps=1,
        logging_enabled=True,
    )

    assert analysis.player_summaries == []
    assert len(analysis.log_records) == 1
    assert analysis.log_records[0].rejection_reason == "low_confidence"


def test_analyze_reports_progress_while_frames_are_still_streaming() -> None:
    video_service = _StreamingVideoServiceStub()
    service = AnalysisService(video_service=video_service, ocr_service=_OCRServiceStub())
    progress_snapshots: list[tuple[int, int]] = []

    def on_progress(value: int) -> None:
        progress_snapshots.append((value, video_service.frames_yielded))

    service.analyze(
        url="https://youtube.com/watch?v=test",
        regions=[(10, 20, 100, 50)],
        start_time=0.0,
        end_time=2.0,
        fps=1,
        on_progress=on_progress,
    )

    assert progress_snapshots
    assert progress_snapshots[0][1] == 1
    assert progress_snapshots[-1][0] == 100


# ---------------------------------------------------------------------------
# T034 – On-screen display-name selection (FR-005/FR-028)
# ---------------------------------------------------------------------------


def test_build_player_summaries_selects_earliest_on_screen_player_name() -> None:
    """The earliest-seen extracted_name (stripped) is used as the display player_name."""
    detections = [
        TextDetection(
            raw_ocr_text="Player: Alice",
            extracted_name="Alice",
            normalized_name="alice",
            region_id="r1",
            frame_time_sec=1.0,
        ),
        TextDetection(
            raw_ocr_text="Player: ALICE",
            extracted_name="ALICE",
            normalized_name="alice",
            region_id="r1",
            frame_time_sec=3.0,
        ),
    ]

    summaries = AnalysisService.build_player_summaries(detections, gap_threshold_sec=5.0)
    assert len(summaries) == 1
    # First-seen form (t=1.0) "Alice" must be chosen, not the later "ALICE"
    assert summaries[0].player_name == "Alice"


def test_us3_analysis_pipeline_regression_downstream_summary_shape_is_unchanged() -> None:
    service = AnalysisService(video_service=_VideoServiceStub(), ocr_service=_OCRServiceStub())

    analysis = service.analyze(
        url="https://youtube.com/watch?v=test",
        regions=[(10, 20, 100, 50)],
        start_time=0.0,
        end_time=60.0,
        fps=1,
    )

    assert len(analysis.player_summaries) == 1
    summary = analysis.player_summaries[0]
    assert summary.player_name == "Raw OCR Name"
    assert summary.start_timestamp == "00:00:12.000"


def test_build_player_summaries_display_name_is_stripped() -> None:
    """Surrounding whitespace in extracted_name is stripped for the display name."""
    detections = [
        TextDetection(
            raw_ocr_text="Player:  Bob ",
            extracted_name="  Bob ",
            normalized_name="bob",
            region_id="r1",
            frame_time_sec=2.0,
        ),
    ]

    summaries = AnalysisService.build_player_summaries(detections, gap_threshold_sec=1.0)

    assert summaries[0].player_name == "Bob"


# ---------------------------------------------------------------------------
# T033 – Recall-first context-matched candidate preservation (FR-034)
# ---------------------------------------------------------------------------


def test_merge_appearance_events_preserves_all_context_matched_candidates() -> None:
    """All non-empty candidates are preserved through event merging, not just patterns."""
    # Simulate detections where some candidates are pattern-matched, others are fallback
    detections = [
        TextDetection(
            raw_ocr_text="Player: Alice",
            extracted_name="Alice",
            normalized_name="alice",
            region_id="r1",
            frame_time_sec=1.0,
            matched_pattern_id="player",  # Pattern-matched
        ),
        TextDetection(
            raw_ocr_text="Random: Text: Here",
            extracted_name="Random: Text: Here",  # No pattern match, fallback
            normalized_name="random: text: here",
            region_id="r2",
            frame_time_sec=2.0,
            matched_pattern_id=None,
        ),
    ]

    # When we build summaries, all detections should be preserved
    summaries = AnalysisService.build_player_summaries(detections, gap_threshold_sec=1.0)

    # Should have 2 distinct entries (different normalized names)
    assert len(summaries) == 2
    normalized_names = {s.normalized_name for s in summaries}
    assert "alice" in normalized_names
    assert "random: text: here" in normalized_names


# ---------------------------------------------------------------------------
# T035 – Appearance-event gap merge tests (FR-030)
# ---------------------------------------------------------------------------


def test_merge_appearance_events_merges_detections_within_gap_threshold() -> None:
    """Detections of the same name within gap_threshold_sec are merged into one event."""
    detections = [
        ("alice", 1.0, "r1"),   # First detection
        ("alice", 1.5, "r1"),   # Within 1.0 sec gap
        ("alice", 4.2, "r2"),   # Outside 1.0 sec gap - new event
    ]

    events = AnalysisService.merge_appearance_events(detections, gap_threshold_sec=1.0)

    assert len(events) == 2
    # Event 1: 1.0 - 1.5
    assert events[0].start_time_sec == 1.0
    assert events[0].end_time_sec == 1.5
    assert events[0].region_ids == {"r1"}
    # Event 2: 4.2 - 4.2
    assert events[1].start_time_sec == 4.2
    assert events[1].end_time_sec == 4.2
    assert events[1].region_ids == {"r2"}


def test_merge_appearance_events_different_names_separate_events() -> None:
    """Different normalized names always generate separate events regardless of time."""
    detections = [
        ("alice", 1.0, "r1"),
        ("bob", 1.1, "r1"),   # Different name, very close in time
        ("alice", 2.0, "r2"),
    ]

    events = AnalysisService.merge_appearance_events(detections, gap_threshold_sec=10.0)

    # Alice detections (1.0 and 2.0) merge into ONE event (within gap)
    # Bob is separate → total 2 events
    assert len(events) == 2
    # Find alice and bob events
    alice_events = [e for e in events if e.normalized_name == "alice"]
    bob_events = [e for e in events if e.normalized_name == "bob"]
    assert len(alice_events) == 1
    assert len(bob_events) == 1
    # Alice spans 1.0-2.0
    assert alice_events[0].start_time_sec == 1.0
    assert alice_events[0].end_time_sec == 2.0


def test_merge_appearance_events_gap_exactly_at_threshold() -> None:
    """Detections exactly at gap_threshold_sec are considered within threshold (<=)."""
    detections = [
        ("alice", 1.0, "r1"),
        ("alice", 3.0, "r1"),  # Exactly 2.0 sec gap
    ]

    events = AnalysisService.merge_appearance_events(detections, gap_threshold_sec=2.0)

    # Should be merged (time_diff <= threshold)
    assert len(events) == 1
    assert events[0].start_time_sec == 1.0
    assert events[0].end_time_sec == 3.0


def test_merge_appearance_events_gap_just_beyond_threshold() -> None:
    """Detections just beyond gap_threshold_sec cause separation into new events."""
    detections = [
        ("alice", 1.0, "r1"),
        ("alice", 3.01, "r1"),  # 2.01 sec gap (just over 2.0 threshold)
    ]

    events = AnalysisService.merge_appearance_events(detections, gap_threshold_sec=2.0)

    # Should be separated into 2 events
    assert len(events) == 2
    assert events[0].end_time_sec == 1.0
    assert events[1].start_time_sec == 3.01
