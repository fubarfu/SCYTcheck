from __future__ import annotations

import contextlib
import json
import re
import socket
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import parse_qs, urlparse

from src.web.api.routes.analysis import AnalysisHandler
from src.web.api.routes.fs import FsHandler
from src.web.api.routes.history import HistoryHandler
from src.web.api.routes.review import ReviewHandler
from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_assets import ReviewAssetsHandler
from src.web.api.routes.review_export import ReviewExportHandler
from src.web.api.routes.review_history import ReviewHistoryHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.api.routes.settings import SettingsHandler
from src.web.api.routes.projects import ProjectsHandler
from src.web.app.review_history_store import ReviewHistoryStore
from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.web.app.session_manager import SessionManager
from src.web.app.config import WebAppConfig, load_web_config


class _AppServices:
    def __init__(self) -> None:
        session_manager = SessionManager()
        sidecar_store = ReviewSidecarStore()
        history_store = ReviewHistoryStore(sidecar_store)
        self.settings = SettingsHandler()
        self.analysis = AnalysisHandler()
        self.fs = FsHandler()
        self.projects = ProjectsHandler(settings_handler=self.settings)
        self.review = ReviewHandler(settings_handler=self.settings)
        self.review_sessions = ReviewSessionHandler(
            session_manager=session_manager,
            history_store=history_store,
        )
        self.review_actions = ReviewActionsHandler(
            session_manager=session_manager,
            history_store=history_store,
        )
        self.review_history = ReviewHistoryHandler(
            session_manager=session_manager,
            history_store=history_store,
        )
        self.review_assets = ReviewAssetsHandler(session_manager=session_manager)
        self.review_export = ReviewExportHandler(session_manager=session_manager)
        self.history = HistoryHandler()

    def flush_pending_review_history(self) -> int:
        return self.review_sessions.flush_all_pending_history("app-close")


class _RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, directory: str, services: _AppServices, **kwargs: Any) -> None:
        self._services = services
        super().__init__(*args, directory=directory, **kwargs)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, status: int, file_path: Path, content_type: str) -> None:
        body = file_path.read_bytes()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length)
        if not raw:
            return {}
        decoded = json.loads(raw.decode("utf-8"))
        return decoded if isinstance(decoded, dict) else {}

    @staticmethod
    def _normalize_api_path(path: str) -> str:
        if path.startswith("/api/"):
            return path.rstrip("/") or "/"
        return path

    def _dispatch_api(self, method: str, path: str) -> bool:
        if path == "/api/health" and method == "GET":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return

        if path == "/api/settings":
            if method == "GET":
                self._send_json(HTTPStatus.OK, self._services.settings.get_settings())
                return True
            if method == "PUT":
                status, body = self._services.settings.put_settings(self._read_json_body())
                self._send_json(status, body)
                return True

        if re.fullmatch(r"/api/settings/validate/?", path) and method == "POST":
            status, body = self._services.settings.post_validate_settings(self._read_json_body())
            self._send_json(status, body)
            return True

        if path == "/api/analysis/preview" and method == "POST":
            status, body = self._services.analysis.post_preview(self._read_json_body())
            self._send_json(status, body)
            return True
        if path == "/api/analysis/start" and method == "POST":
            status, body = self._services.analysis.post_start(self._read_json_body())
            self._send_json(status, body)
            return True

        progress_match = re.fullmatch(r"/api/analysis/progress/([^/]+)", path)
        if progress_match and method == "GET":
            status, body = self._services.analysis.get_progress(progress_match.group(1))
            self._send_json(status, body)
            return True

        stop_match = re.fullmatch(r"/api/analysis/stop/([^/]+)", path)
        if stop_match and method == "POST":
            status, body = self._services.analysis.post_stop(stop_match.group(1))
            self._send_json(status, body)
            return True

        result_match = re.fullmatch(r"/api/analysis/result/([^/]+)", path)
        if result_match and method == "GET":
            status, body = self._services.analysis.get_result(result_match.group(1))
            self._send_json(status, body)
            return True

        if path in {"/api/review/sessions", "/api/review/sessions/"} and method == "GET":
            status, body = self._services.review_sessions.get_sessions()
            self._send_json(status, body)
            return True

        if path == "/api/history/videos" and method == "GET":
            query = parse_qs(urlparse(self.path).query)
            status, body = self._services.history.get_videos(
                {
                    "include_deleted": query.get("include_deleted", ["false"])[0],
                    "limit": query.get("limit", ["200"])[0],
                }
            )
            self._send_json(status, body)
            return True

        if re.fullmatch(r"/api/projects/?", path) and method == "GET":
            status, body = self._services.projects.get_projects()
            self._send_json(status, body)
            return True

        project_match = re.fullmatch(r"/api/projects/([^/]+)/?", path)
        if project_match and method == "GET":
            status, body = self._services.projects.get_projects_detail(project_match.group(1))
            self._send_json(status, body)
            return True

        if path == "/api/history/merge-run" and method == "POST":
            status, body = self._services.history.post_merge_run(self._read_json_body())
            self._send_json(status, body)
            return True

        if path == "/api/history/reopen" and method == "POST":
            status, body = self._services.history.post_reopen(self._read_json_body())
            self._send_json(status, body)
            return True

        history_match = re.fullmatch(r"/api/history/videos/([^/]+)", path)
        if history_match and method == "GET":
            status, body = self._services.history.get_video(history_match.group(1))
            self._send_json(status, body)
            return True
        if history_match and method == "DELETE":
            status, body = self._services.history.delete_video(history_match.group(1))
            self._send_json(status, body)
            return True

        if path == "/api/review/context" and method == "GET":
            query = parse_qs(urlparse(self.path).query)
            status, body = self._services.review.get_review_context(
                {"video_id": query.get("video_id", [""])[0]}
            )
            self._send_json(status, body)
            return True

        if path == "/api/review/action" and method == "PUT":
            status, body = self._services.review.put_review_action(self._read_json_body())
            self._send_json(status, body)
            return True

        if path == "/api/review/sessions/load" and method == "POST":
            status, body = self._services.review_sessions.post_load(self._read_json_body())
            self._send_json(status, body)
            return True

        review_workspace_match = re.fullmatch(r"/api/review/workspaces/([^/]+)", path)
        if review_workspace_match and method == "GET":
            query = parse_qs(urlparse(self.path).query)
            status, body = self._services.review_history.get_workspace(
                review_workspace_match.group(1),
                session_id=query.get("session_id", [None])[0],
            )
            self._send_json(status, body)
            return True

        review_history_list_match = re.fullmatch(r"/api/review/workspaces/([^/]+)/history", path)
        if review_history_list_match and method == "GET":
            query = parse_qs(urlparse(self.path).query)
            status, body = self._services.review_history.get_history(
                review_history_list_match.group(1),
                session_id=query.get("session_id", [None])[0],
            )
            self._send_json(status, body)
            return True

        review_history_entry_match = re.fullmatch(r"/api/review/workspaces/([^/]+)/history/([^/]+)", path)
        if review_history_entry_match and method == "GET":
            query = parse_qs(urlparse(self.path).query)
            status, body = self._services.review_history.get_history_entry(
                review_history_entry_match.group(1),
                review_history_entry_match.group(2),
                session_id=query.get("session_id", [None])[0],
            )
            self._send_json(status, body)
            return True

        review_restore_match = re.fullmatch(r"/api/review/workspaces/([^/]+)/history/([^/]+)/restore", path)
        if review_restore_match and method == "POST":
            status, body = self._services.review_history.post_restore(
                review_restore_match.group(1),
                review_restore_match.group(2),
                self._read_json_body(),
            )
            self._send_json(status, body)
            return True

        scan_match = path == "/api/review/sessions/scan"
        if scan_match and method == "GET":
            query = parse_qs(urlparse(self.path).query)
            directory_path = query.get("directory_path", [""])[0]
            status, body = self._services.review_sessions.get_scan_directory(directory_path)
            self._send_json(status, body)
            return True

        thresholds_match = re.fullmatch(r"/api/review/sessions/([^/]+)/thresholds", path)
        if thresholds_match and method == "PATCH":
            status, body = self._services.review_sessions.patch_thresholds(
                thresholds_match.group(1),
                self._read_json_body(),
            )
            self._send_json(status, body)
            return True

        recalculate_match = re.fullmatch(r"/api/review/sessions/([^/]+)/recalculate/?", path)
        if recalculate_match and method == "POST":
            status, body = self._services.review_sessions.post_recalculate(recalculate_match.group(1))
            self._send_json(status, body)
            return True

        actions_match = re.fullmatch(r"/api/review/sessions/([^/]+)/actions", path)
        if actions_match and method == "POST":
            status, body = self._services.review_actions.post_action(
                actions_match.group(1),
                self._read_json_body(),
            )
            self._send_json(status, body)
            return True

        flush_on_close_match = re.fullmatch(r"/api/review/sessions/([^/]+)/flush-on-close", path)
        if flush_on_close_match and method == "POST":
            status, body = self._services.review_sessions.post_flush_on_close(flush_on_close_match.group(1))
            self._send_json(status, body)
            return True

        undo_match = re.fullmatch(r"/api/review/sessions/([^/]+)/undo", path)
        if undo_match and method == "POST":
            status, body = self._services.review_actions.post_undo(undo_match.group(1))
            self._send_json(status, body)
            return True

        thumb_png_match = re.fullmatch(r"/api/review/sessions/([^/]+)/thumbnails/([^/]+)\.png", path)
        if thumb_png_match and method == "GET":
            session_id, candidate_id = thumb_png_match.groups()
            asset_path = self._services.review_assets.resolve_thumbnail_path(session_id, candidate_id)
            if asset_path is None:
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {
                        "error": "not_found",
                        "message": f"No thumbnail available for candidate {candidate_id}",
                    },
                )
                return True
            self._send_file(HTTPStatus.OK, asset_path, "image/png")
            return True

        thumb_match = re.fullmatch(r"/api/review/sessions/([^/]+)/thumbnails/([^/]+)", path)
        if thumb_match and method == "GET":
            status, body = self._services.review_assets.get_thumbnail(
                thumb_match.group(1),
                thumb_match.group(2),
            )
            self._send_json(status, body)
            return True

        asset_match = re.fullmatch(r"/api/assets/(frames|cache)/([^/]+)/([^/]+)\.png", path)
        if asset_match and method == "GET":
            asset_kind, session_id, candidate_id = asset_match.groups()
            asset_path = self._services.review_assets.resolve_thumbnail_path(
                session_id,
                candidate_id,
                asset_kind=asset_kind,
            )
            if asset_path is None:
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {
                        "error": "not_found",
                        "message": f"No thumbnail available for candidate {candidate_id}",
                    },
                )
                return True
            self._send_file(HTTPStatus.OK, asset_path, "image/png")
            return True

        export_match = re.fullmatch(r"/api/review/sessions/([^/]+)/export", path)
        if export_match and method == "POST":
            status, body = self._services.review_export.post_export(export_match.group(1))
            self._send_json(status, body)
            return True

        session_match = re.fullmatch(r"/api/review/sessions/([^/]+)", path)
        if session_match and method == "GET":
            status, body = self._services.review_sessions.get_session(session_match.group(1))
            self._send_json(status, body)
            return True

        if path == "/api/fs/pick-folder" and method == "GET":
            query = parse_qs(urlparse(self.path).query)
            initial_dir = query.get("initial_dir", [""])[0]
            status, body = self._services.fs.get_pick_folder(initial_dir)
            self._send_json(status, body)
            return True

        self._send_json(HTTPStatus.NOT_FOUND, {
            "error": "not_found",
            "message": f"No route for {method} {path}",
        })
        return True

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        request_path = self._normalize_api_path(parsed.path or "/")

        if request_path.startswith("/api/"):
            self._dispatch_api("GET", request_path)
            return

        if not request_path.startswith("/api/"):
            translated = Path(self.translate_path(request_path))
            if request_path in {"/", ""} or not translated.exists() or translated.is_dir():
                self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        request_path = self._normalize_api_path(parsed.path or "/")
        if self._dispatch_api("POST", request_path):
            return

    def do_PUT(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        request_path = self._normalize_api_path(parsed.path or "/")
        if self._dispatch_api("PUT", request_path):
            return

    def do_PATCH(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        request_path = self._normalize_api_path(parsed.path or "/")
        if self._dispatch_api("PATCH", request_path):
            return

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        request_path = self._normalize_api_path(parsed.path or "/")
        if self._dispatch_api("DELETE", request_path):
            return


class LocalWebServer:
    """Small local static server used by the web runtime bootstrap."""

    def __init__(self, config: WebAppConfig | None = None) -> None:
        self.config = config or load_web_config()
        self._services = _AppServices()
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
            return _RequestHandler(
                *args,
                directory=str(dist_dir),
                services=self._services,
                **kwargs,
            )

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
        self._services.flush_pending_review_history()
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None
        self._active_port = None
