from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_sessions import ReviewSessionHandler


def test_session_picker_directory_scan_lists_csv_files(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text("PlayerName,StartTimestamp\nAlice,1\n", encoding="utf-8")
    (tmp_path / "b.csv").write_text("PlayerName,StartTimestamp\nBob,2\n", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("x", encoding="utf-8")

    handler = ReviewSessionHandler()
    status, body = handler.get_scan_directory(str(tmp_path))
    assert status == 200
    assert len(body["files"]) == 2
