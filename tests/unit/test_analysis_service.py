from src.services.analysis_service import AnalysisService
from src.data.models import ContextPattern, TextDetection


class _VideoServiceStub:
    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        del url, start_time, end_time, fps, quality
        yield 12.0, [[0]]


class _OCRServiceStub:
    def detect_text(self, frame, region):
        del frame, region
        return ["Raw OCR Name"]

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
    service = AnalysisService(video_service=_VideoServiceStub(), ocr_service=_OCRServiceDiagnosticsStub())

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
