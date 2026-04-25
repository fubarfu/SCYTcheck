from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_assets import ReviewAssetsHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.session_manager import SessionManager


def _make_session(tmp_path: Path) -> tuple[str, Path, SessionManager]:
    csv_path = tmp_path / "match.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,0.0\n", encoding="utf-8"
    )
    manager = SessionManager()
    handler = ReviewSessionHandler(session_manager=manager)
    _, body = handler.post_load({"csv_path": str(csv_path)})
    return body["session_id"], csv_path, manager


def test_thumbnail_returns_404_when_no_frame_exists(tmp_path: Path) -> None:
    session_id, csv_path, manager = _make_session(tmp_path)
    assets = ReviewAssetsHandler(session_manager=manager, cache_root=tmp_path / "cache")
    status, body = assets.get_thumbnail(session_id, "cand_unknown")
    assert status == 404


def test_thumbnail_returns_url_when_persisted_frame_exists(tmp_path: Path) -> None:
    session_id, csv_path, manager = _make_session(tmp_path)
    # Create a fake persisted frame
    frames_dir = csv_path.parent / f"{csv_path.stem}_frames"
    frames_dir.mkdir()
    (frames_dir / "cand_1.png").write_bytes(b"FAKEPNG")

    assets = ReviewAssetsHandler(session_manager=manager, cache_root=tmp_path / "cache")
    status, body = assets.get_thumbnail(session_id, "cand_1")
    assert status == 200
    assert "thumbnail_url" in body
    assert body["thumbnail_url"] == f"/api/assets/frames/{session_id}/cand_1.png"


def test_session_source_type_local_file(tmp_path: Path) -> None:
    """Verify source_type defaults to local_file when no sidecar present."""
    session_id, csv_path, manager = _make_session(tmp_path)
    state = manager.get(session_id)
    assert state is not None
    assert state.payload.get("source_type") == "local_file"


def test_session_youtube_deep_link_source_type(tmp_path: Path) -> None:
    """Verify youtube_url source_type is preserved from sidecar."""
    import json

    csv_path = tmp_path / "yt_match.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nBob,1.0\n", encoding="utf-8"
    )
    sidecar = csv_path.with_suffix(".review.json")
    sidecar.write_text(
        json.dumps(
            {"source_type": "youtube_url", "source_value": "https://youtube.com/watch?v=abc"}
        ),
        encoding="utf-8",
    )

    manager = SessionManager()
    handler = ReviewSessionHandler(session_manager=manager)
    _, body = handler.post_load({"csv_path": str(csv_path)})
    session_id = body["session_id"]

    state = manager.get(session_id)
    assert state is not None
    assert state.payload.get("source_type") == "youtube_url"
    assert state.payload.get("source_value") == "https://youtube.com/watch?v=abc"
