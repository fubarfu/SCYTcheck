from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import threading
import webbrowser

from src.web.app.config import WebAppConfig, load_web_config
from src.web.app.server import LocalWebServer


@dataclass
class LauncherState:
    server: LocalWebServer


_LAUNCHER_LOCK = threading.Lock()
_ACTIVE_STATE: LauncherState | None = None


class AppLauncher:
    """Single-instance launcher that starts local server and opens browser."""

    def __init__(
        self,
        config: WebAppConfig | None = None,
        browser_opener: Callable[[str], bool] | None = None,
    ) -> None:
        self.config = config or load_web_config()
        self.browser_opener = browser_opener or webbrowser.open_new_tab

    def start(self) -> str:
        global _ACTIVE_STATE

        with _LAUNCHER_LOCK:
            if _ACTIVE_STATE is None:
                server = LocalWebServer(config=self.config)
                server.start()
                _ACTIVE_STATE = LauncherState(server=server)

            url = f"{_ACTIVE_STATE.server.base_url}/analysis"
            if self.config.auto_open_browser:
                self.browser_opener(url)
            return url

    def stop(self) -> None:
        global _ACTIVE_STATE

        with _LAUNCHER_LOCK:
            if _ACTIVE_STATE is None:
                return
            _ACTIVE_STATE.server.stop()
            _ACTIVE_STATE = None
