from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WebAppConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    auto_open_browser: bool = True
    startup_timeout_seconds: float = 5.0
    frontend_dist_dir: Path = Path("src/web/frontend/dist")


DEFAULT_WEB_CONFIG = WebAppConfig()


def load_web_config() -> WebAppConfig:
    """Load web runtime configuration from environment variables with safe defaults."""
    host = os.getenv("SCYTCHECK_WEB_HOST", DEFAULT_WEB_CONFIG.host)
    port_raw = os.getenv("SCYTCHECK_WEB_PORT", str(DEFAULT_WEB_CONFIG.port))
    auto_open = os.getenv("SCYTCHECK_WEB_OPEN_BROWSER", "1")
    try:
        port = int(port_raw)
    except ValueError:
        port = DEFAULT_WEB_CONFIG.port

    return WebAppConfig(
        host=host,
        port=max(1024, min(65535, port)),
        auto_open_browser=auto_open.strip() not in {"0", "false", "False"},
        startup_timeout_seconds=DEFAULT_WEB_CONFIG.startup_timeout_seconds,
        frontend_dist_dir=Path(
            os.getenv("SCYTCHECK_WEB_DIST_DIR", str(DEFAULT_WEB_CONFIG.frontend_dist_dir))
        ),
    )
