from __future__ import annotations

from src.services.history_service import HistoryService
from src.web.app.history_store import HistoryStore


def test_merge_identity_merges_same_canonical_and_duration(tmp_path) -> None:
    store = HistoryStore(index_path=tmp_path / "video_history.json")
    service = HistoryService(store=store)

    output = tmp_path / "out"
    output.mkdir()
    csv1 = output / "run1.csv"
    csv1.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nA,1\n", encoding="utf-8")
    csv2 = output / "run2.csv"
    csv2.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nB,2\n", encoding="utf-8")

    context = {
        "scan_region": {"x": 1, "y": 1, "width": 10, "height": 10},
        "context_patterns": [],
        "analysis_settings": {},
    }
    first = service.merge_run(
        source_type="youtube_url",
        source_value="https://youtube.com/watch?v=abc123",
        canonical_source="youtube:abc123",
        duration_seconds=100,
        result_csv_path=str(csv1),
        output_folder=str(output),
        context=context,
    )
    second = service.merge_run(
        source_type="youtube_url",
        source_value="https://youtube.com/watch?v=abc123",
        canonical_source="youtube:abc123",
        duration_seconds=100,
        result_csv_path=str(csv2),
        output_folder=str(output),
        context=context,
    )

    assert second["history_id"] == first["history_id"]
    assert second["merged"] is True
    assert second["run_count"] == 2


def test_missing_duration_creates_potential_duplicate(tmp_path) -> None:
    store = HistoryStore(index_path=tmp_path / "video_history.json")
    service = HistoryService(store=store)

    output = tmp_path / "out"
    output.mkdir()
    csv_path = output / "result.csv"
    csv_path.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nA,1\n", encoding="utf-8")

    context = {
        "scan_region": {"x": 1, "y": 1, "width": 10, "height": 10},
        "context_patterns": [],
        "analysis_settings": {},
    }
    merged = service.merge_run(
        source_type="local_file",
        source_value=str(tmp_path / "video.mp4"),
        canonical_source=str(tmp_path / "video.mp4").lower(),
        duration_seconds=None,
        result_csv_path=str(csv_path),
        output_folder=str(output),
        context=context,
    )

    assert merged["merged"] is False
    assert merged["potential_duplicate"] is True
