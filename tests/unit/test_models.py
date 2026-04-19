from src.data.models import AnalysisRuntimeMetrics, GatingStats, TimingBreakdown, VideoAnalysis


def test_add_detection_groups_same_region_and_text() -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=abc")

    analysis.add_detection("PlayerOne", (10, 20, 100, 30))
    analysis.add_detection("playerone", (10, 20, 100, 30))

    assert len(analysis.text_strings) == 1
    assert analysis.text_strings[0].frequency == 2


def test_gating_stats_defaults_and_zero_percentage() -> None:
    stats = GatingStats()

    assert stats.total_frame_region_pairs == 0
    assert stats.ocr_executed_count == 0
    assert stats.ocr_skipped_count == 0
    assert stats.skip_percentage == 0.0


def test_gating_stats_skip_percentage_calculation() -> None:
    stats = GatingStats(total_frame_region_pairs=10, ocr_executed_count=7, ocr_skipped_count=3)

    assert stats.skip_percentage == 30.0


def test_timing_breakdown_defaults_are_non_negative() -> None:
    timing = TimingBreakdown()

    assert timing.decode_ms == 0.0
    assert timing.gating_ms == 0.0
    assert timing.ocr_ms == 0.0
    assert timing.post_processing_ms == 0.0
    assert timing.total_ms == 0.0


def test_runtime_metrics_default_contract() -> None:
    metrics = AnalysisRuntimeMetrics()

    assert metrics.timing_breakdown is None
    assert metrics.instrumentation_enabled is False
    assert metrics.instrumentation_overhead_pct == 0.0


def test_video_analysis_accepts_runtime_metrics() -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=abc")
    analysis.runtime_metrics = AnalysisRuntimeMetrics(
        timing_breakdown=TimingBreakdown(total_ms=12.5),
        instrumentation_enabled=True,
    )

    assert analysis.runtime_metrics is not None
    assert analysis.runtime_metrics.instrumentation_enabled is True
    assert analysis.runtime_metrics.timing_breakdown is not None
    assert analysis.runtime_metrics.timing_breakdown.total_ms == 12.5
