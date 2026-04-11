from pathlib import Path

from src.data.models import VideoAnalysis
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
