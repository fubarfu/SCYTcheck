from __future__ import annotations

from pathlib import Path

from src.web.app.config import WebAppConfig
from src.web.app.launcher import AppLauncher


def test_launcher_rerun_reuses_existing_server(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "index.html").write_text("<html><body>Ready</body></html>", encoding="utf-8")

    opened_urls: list[str] = []

    def fake_open(url: str) -> bool:
        opened_urls.append(url)
        return True

    launcher_a = AppLauncher(
        config=WebAppConfig(port=0, frontend_dist_dir=dist_dir, auto_open_browser=True),
        browser_opener=fake_open,
    )
    launcher_b = AppLauncher(
        config=WebAppConfig(port=0, frontend_dist_dir=dist_dir, auto_open_browser=True),
        browser_opener=fake_open,
    )

    try:
        url_a = launcher_a.start()
        url_b = launcher_b.start()

        assert url_a == url_b
        assert opened_urls == [url_a, url_b]
    finally:
        launcher_a.stop()
