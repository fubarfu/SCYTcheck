from __future__ import annotations

from src.web.api.schemas import HistoryMergeRunRequestDTO, SchemaValidationError
from src.web.app.history_store import canonicalize_source, make_merge_key, parse_duration_seconds


def test_parse_duration_seconds_guards_invalid() -> None:
    assert parse_duration_seconds("10") == 10
    assert parse_duration_seconds(None) is None
    assert parse_duration_seconds("abc") is None
    assert parse_duration_seconds(-1) is None


def test_canonicalize_source_for_youtube_and_local(tmp_path) -> None:
    assert canonicalize_source("youtube_url", "https://www.youtube.com/watch?v=AbC123") == "youtube:abc123"
    canonical_local = canonicalize_source("local_file", str(tmp_path / "Video.mp4"))
    assert canonical_local.endswith("video.mp4")


def test_make_merge_key_requires_duration() -> None:
    assert make_merge_key("youtube:abc", 120) == "youtube:abc|120"
    assert make_merge_key("youtube:abc", None) is None


def test_history_merge_dto_requires_context() -> None:
    payload = {
        "source_type": "local_file",
        "source_value": "C:/video.mp4",
        "canonical_source": "c:/video.mp4",
        "duration_seconds": 120,
        "result_csv_path": "C:/out/result.csv",
        "output_folder": "C:/out",
    }
    import pytest

    with pytest.raises(SchemaValidationError, match="context"):
        HistoryMergeRunRequestDTO.from_payload(payload)
