from __future__ import annotations

import contextlib
import json
import socket
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

from src.web.app.config import WebAppConfig, load_web_config


class _RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, directory: str, **kwargs: Any) -> None:
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/health":
            body = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        parsed = urlparse(self.path)
        request_path = parsed.path or "/"
        if not request_path.startswith("/api/"):
            translated = Path(self.translate_path(request_path))
            if request_path in {"/", ""} or not translated.exists() or translated.is_dir():
                self.path = "/index.html"
        return super().do_GET()


class LocalWebServer:
    """Small local static server used by the web runtime bootstrap."""

    def __init__(self, config: WebAppConfig | None = None) -> None:
        self.config = config or load_web_config()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._active_port: int | None = None
        self.startup_duration_seconds: float = 0.0

    @property
    def base_url(self) -> str:
        port = self._active_port or self.config.port
        return f"http://{self.config.host}:{port}"

    @staticmethod
    def _find_available_port(host: str) -> int:
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.bind((host, 0))
            sock.listen(1)
            return int(sock.getsockname()[1])

    def start(self) -> None:
        if self._server is not None:
            return
        startup_started_at = perf_counter()

        dist_dir = Path(self.config.frontend_dist_dir)
        dist_dir.mkdir(parents=True, exist_ok=True)

        def handler(*args: Any, **kwargs: Any) -> _RequestHandler:
            return _RequestHandler(*args, directory=str(dist_dir), **kwargs)

        target_port = self.config.port
        try:
            self._server = ThreadingHTTPServer((self.config.host, target_port), handler)
        except OSError:
            target_port = self._find_available_port(self.config.host)
            self._server = ThreadingHTTPServer((self.config.host, target_port), handler)

        self._active_port = int(self._server.server_address[1])
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self.startup_duration_seconds = perf_counter() - startup_started_at

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None
        self._active_port = None
