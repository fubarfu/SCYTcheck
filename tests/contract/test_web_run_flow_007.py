from __future__ import annotations

import time
from pathlib import Path

from src.data.models import PlayerSummary, TextDetection, VideoAnalysis
from src.web.api.routes.analysis import AnalysisHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.review_sidecar_store import ReviewSidecarStore


class _FakeVideoService:
    def get_video_info(self, source: str, quality: str = "best") -> dict[str, object]:
        del source, quality
        return {"duration": 5.0, "width": 1920, "height": 1080}


class _FakeAnalysisService:
    def __init__(self) -> None:
        self.video_service = _FakeVideoService()

    def analyze(self, **kwargs) -> VideoAnalysis:
        on_progress = kwargs.get("on_progress")
        if on_progress is not None:
            on_progress(25)
            on_progress(100)

        analysis = VideoAnalysis(url=str(kwargs["url"]))
        analysis.detections = [
            TextDetection(
                raw_ocr_text="PlayerAlpha",
                extracted_name="PlayerAlpha",
                normalized_name="playeralpha",
                region_id="10:20:120:40",
                frame_time_sec=3.5,
                matched_pattern_id="pattern-1",
            )
        ]
        analysis.player_summaries = [
            PlayerSummary(
                player_name="PlayerAlpha",
                start_timestamp="00:00:03.500",
                normalized_name="playeralpha",
                occurrence_count=1,
                first_seen_sec=3.5,
                last_seen_sec=3.5,
                representative_region="10:20:120:40",
            )
        ]
        return analysis


def test_analysis_start_writes_csv_and_review_sidecar(tmp_path: Path, monkeypatch) -> None:
    handler = AnalysisHandler()
    monkeypatch.setattr(
        handler,
        "_create_analysis_service",
        lambda source_type, advanced: _FakeAnalysisService(),
    )

    status, body = handler.post_start(
        {
            "source_type": "youtube_url",
            "source_value": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "output_folder": str(tmp_path),
            "output_filename": "result.csv",
            "scan_region": {"x": 10, "y": 20, "width": 120, "height": 40},
        }
    )

    assert status == 202
    run_id = body["run_id"]

    for _ in range(40):
        progress = handler.get_progress(run_id)[1]
        if progress["status"] == "completed":
            break
        time.sleep(0.05)

    progress = handler.get_progress(run_id)[1]
    assert progress["status"] == "completed"

    video_id = ReviewSidecarStore.make_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    csv_path = tmp_path / ".scyt_review_workspaces" / video_id / "result.csv"
    assert csv_path.exists()
    assert "PlayerAlpha" in csv_path.read_text(encoding="utf-8")

    sidecar_payload = ReviewSidecarStore().load(csv_path)
    assert sidecar_payload is not None
    assert sidecar_payload["source_type"] == "youtube_url"
    assert sidecar_payload["candidates"][0]["extracted_name"] == "PlayerAlpha"


def test_review_session_load_uses_csv_rows_when_sidecar_missing(tmp_path: Path) -> None:
    csv_path = tmp_path / "result.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,00:00:10.000\nBob,00:00:12.000\n",
        encoding="utf-8",
    )

    handler = ReviewSessionHandler()
    status, body = handler.post_load({"csv_path": str(csv_path)})

    assert status == 200
    session_status, session_body = handler.get_session(body["session_id"])
    assert session_status == 200
    assert [candidate["extracted_name"] for candidate in session_body["candidates"]] == ["Alice", "Bob"]


def test_analysis_start_rejects_scan_region_outside_video_bounds(
    tmp_path: Path, monkeypatch
) -> None:
    handler = AnalysisHandler()
    monkeypatch.setattr(
        handler,
        "_create_analysis_service",
        lambda source_type, advanced: _FakeAnalysisService(),
    )

    status, body = handler.post_start(
        {
            "source_type": "youtube_url",
            "source_value": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "output_folder": str(tmp_path),
            "output_filename": "result.csv",
            "scan_region": {"x": 1900, "y": 20, "width": 120, "height": 40},
        }
    )

    assert status == 400
    assert "exceeds frame bounds" in body["message"]
