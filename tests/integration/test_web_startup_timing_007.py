from __future__ import annotations

from pathlib import Path
from time import perf_counter

from src.web.app.config import WebAppConfig
from src.web.app.server import LocalWebServer


def test_web_startup_under_sc007_threshold(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "index.html").write_text("<html><body>SCYTcheck</body></html>", encoding="utf-8")

    server = LocalWebServer(config=WebAppConfig(port=0, frontend_dist_dir=dist_dir))
    start = perf_counter()
    server.start()
    elapsed = perf_counter() - start
    try:
        assert elapsed <= 5.0
        assert server.startup_duration_seconds <= 5.0
    finally:
        server.stop()
