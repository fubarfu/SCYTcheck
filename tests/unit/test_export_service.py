from pathlib import Path
from datetime import datetime

from src.data.models import PlayerSummary, VideoAnalysis
from src.services.export_service import ExportService


def test_export_to_csv_writes_headers_and_rows(tmp_path: Path) -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=abc")
    analysis.add_detection("SampleText", (1, 2, 3, 4))

    service = ExportService()
    exported = service.export_to_csv(analysis, str(tmp_path), "output.csv")

    assert exported.exists()
    content = exported.read_text(encoding="utf-8")
    assert "Text,X,Y,Width,Height,Frequency" in content
    assert "SampleText,1,2,3,4,1" in content


def test_extract_youtube_video_id() -> None:
    """Test video ID extraction from various YouTube URL formats."""
    service = ExportService()
    
    # Standard youtube.com URL
    assert service.extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    # youtube.com URL with additional parameters
    assert service.extract_youtube_video_id("https://youtube.com/watch?v=abc123&t=10s&list=xyz") == "abc123"
    
    # youtu.be short URL
    assert service.extract_youtube_video_id("https://youtu.be/shorturl123") == "shorturl123"
    
    # youtu.be with query parameters
    assert service.extract_youtube_video_id("https://youtu.be/vid456?t=5") == "vid456"


def test_extract_youtube_video_id_invalid() -> None:
    """Test that invalid URLs raise ValueError."""
    service = ExportService()
    
    try:
        service.extract_youtube_video_id("https://example.com/video")
        assert False, "Should raise ValueError for non-YouTube URL"
    except ValueError:
        pass
    
    try:
        service.extract_youtube_video_id("https://youtube.com/channel/UCxyz")
        assert False, "Should raise ValueError for non-watch URL"
    except ValueError:
        pass


def test_generate_filename() -> None:
    """Test auto-filename generation with various inputs."""
    service = ExportService()
    test_time = datetime(2026, 4, 11, 14, 30, 45)
    
    # Basic youtube.com URL
    filename = service.generate_filename("https://youtube.com/watch?v=test123", test_time)
    assert filename == "scytcheck_test123_20260411-143045.csv"
    
    # youtu.be short URL
    filename = service.generate_filename("https://youtu.be/vid456", test_time)
    assert filename == "scytcheck_vid456_20260411-143045.csv"
    
    # URL with query parameters
    filename = service.generate_filename("https://youtube.com/watch?v=abc&t=10s&list=xyz", test_time)
    assert filename == "scytcheck_abc_20260411-143045.csv"


def test_generate_filename_uses_current_time_when_not_specified() -> None:
    """Test that generate_filename uses current time by default."""
    service = ExportService()
    
    filename = service.generate_filename("https://youtube.com/watch?v=testid")
    
    # Should contain video ID and timestamp format
    assert "scytcheck_testid_" in filename
    assert filename.endswith(".csv")
    
    # Check timestamp format YYYYMMDD-HHMMSS
    parts = filename.replace("scytcheck_", "").replace(".csv", "").split("_")
    timestamp_part = parts[-1]
    assert len(timestamp_part) == 15  # YYYYMMDD-HHMMSS
    assert timestamp_part[8] == "-"


def test_export_player_summary_schema_order(tmp_path: Path) -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=abc")
    analysis.set_player_summaries(
        [
            PlayerSummary(
                player_name="Alice",
                normalized_name="alice",
                occurrence_count=3,
                first_seen_sec=1.0,
                last_seen_sec=9.5,
                representative_region="r1",
            )
        ]
    )

    service = ExportService()
    exported = service.export_to_csv(analysis, str(tmp_path), "summary.csv")
    lines = exported.read_text(encoding="utf-8").splitlines()

    assert lines[0] == "PlayerName,NormalizedName,OccurrenceCount,FirstSeenSec,LastSeenSec,RepresentativeRegion"
    assert lines[1] == "Alice,alice,3,1.0,9.5,r1"

