from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen

from src.web.app.config import WebAppConfig
from src.web.app.server import LocalWebServer


def test_navigation_routes_do_not_require_reload(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "index.html").write_text("<html><body>SPA Shell</body></html>", encoding="utf-8")

    server = LocalWebServer(config=WebAppConfig(port=0, frontend_dist_dir=dist_dir))
    server.start()

    try:
        for route in ("/", "/analysis", "/review"):
            with urlopen(f"{server.base_url}{route}") as response:  # noqa: S310
                body = response.read().decode("utf-8")
                assert response.status == 200
                assert "SPA Shell" in body
    finally:
        server.stop()
