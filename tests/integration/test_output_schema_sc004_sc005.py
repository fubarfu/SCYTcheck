from __future__ import annotations

from src.data.models import PlayerSummary, VideoAnalysis
from src.services.export_service import ExportService


def test_sc004_sc005_summary_output_schema_and_timestamp(tmp_path) -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=test")
    analysis.set_player_summaries(
        [
            PlayerSummary(
                player_name="Alice",
                start_timestamp="00:00:01.234",
                normalized_name="alice",
                occurrence_count=1,
                first_seen_sec=1.234,
                last_seen_sec=1.234,
                representative_region="10:20:100:50",
            )
        ]
    )

    exported = ExportService().export_to_csv(analysis, str(tmp_path), "summary.csv")
    lines = exported.read_text(encoding="utf-8").splitlines()

    assert lines == [
        "PlayerName,StartTimestamp",
        "Alice,00:00:01.234",
    ]
