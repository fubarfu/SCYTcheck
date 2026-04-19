from __future__ import annotations

from src.data.models import GatingStats, VideoAnalysis
from src.services.export_service import ExportService


def test_gating_stats_schema_persists_on_video_analysis_and_formats_for_export() -> None:
    stats = GatingStats(
        total_frame_region_pairs=100,
        ocr_executed_count=72,
        ocr_skipped_count=28,
        gating_enabled=True,
        gating_threshold=0.02,
    )
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=stats", gating_stats=stats)

    assert analysis.gating_stats is not None
    assert analysis.gating_stats.total_frame_region_pairs == 100
    assert analysis.gating_stats.ocr_executed_count == 72
    assert analysis.gating_stats.ocr_skipped_count == 28
    assert analysis.gating_stats.gating_enabled is True
    assert analysis.gating_stats.gating_threshold == 0.02

    summary = ExportService.format_gating_summary(analysis.gating_stats)
    assert "Evaluated 100" in summary
    assert "OCR Executed 72" in summary
    assert "OCR Skipped 28 (28.0%)" in summary
