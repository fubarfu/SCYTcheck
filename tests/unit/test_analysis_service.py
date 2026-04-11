from src.services.analysis_service import AnalysisService
from src.data.models import TextDetection


def test_normalize_name_lower_trim_and_collapse_spaces() -> None:
    assert AnalysisService.normalize_name("  Player   One  ") == "player one"


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
