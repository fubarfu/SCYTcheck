from __future__ import annotations

from pathlib import Path

from src.web.app.config import WebAppConfig
from src.web.app.launcher import AppLauncher


def test_launcher_opens_localhost_analysis_view(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "index.html").write_text("<html><body>Analysis</body></html>", encoding="utf-8")

    opened_urls: list[str] = []

    def fake_open(url: str) -> bool:
        opened_urls.append(url)
        return True

    launcher = AppLauncher(
        config=WebAppConfig(port=0, frontend_dist_dir=dist_dir, auto_open_browser=True),
        browser_opener=fake_open,
    )

    try:
        url = launcher.start()
        assert url.startswith("http://127.0.0.1:")
        assert url.endswith("/analysis")
        assert opened_urls == [url]
    finally:
        launcher.stop()
