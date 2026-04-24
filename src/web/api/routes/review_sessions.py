from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from src.web.app.grouping_service import GroupingService, GroupingThresholds
from src.web.app.recommendation_service import RecommendationService
from src.web.app.result_schema_validator import ResultSchemaValidator
from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.web.app.session_manager import SessionManager


class ReviewSessionHandler:
    """HTTP-style handler for review session load/list/get endpoints."""

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        validator: ResultSchemaValidator | None = None,
    ) -> None:
        self.sessions = session_manager or SessionManager()
        self.validator = validator or ResultSchemaValidator()
        self._sidecar = ReviewSidecarStore()

    def post_load(self, payload: dict[str, Any]) -> tuple[int, dict]:
        csv_path_raw = str(payload.get("csv_path", "")).strip()
        if not csv_path_raw:
            return 400, {"error": "validation_error", "message": "csv_path is required"}

        csv_path = Path(csv_path_raw)
        if not csv_path.exists():
            return 404, {"error": "not_found", "message": f"File not found: {csv_path_raw}"}

        validation = self.validator.validate(csv_path)
        if not validation.is_valid:
            return 422, {
                "error": "invalid_schema",
                "message": validation.error or "Unsupported schema version",
                "schema_version": validation.schema_version,
                "missing_columns": validation.missing_columns,
            }

        session_id = f"sess_{csv_path.stem}_{uuid.uuid4().hex[:8]}"
        existing = self._sidecar.load(csv_path) or {}
        source_type = existing.get("source_type", "local_file")
        source_value = existing.get("source_value", "")

        session_payload: dict[str, Any] = {
            "schema_version": validation.schema_version,
            "source_type": source_type,
            "source_value": source_value,
            "candidates": existing.get("candidates", []),
            "action_history": existing.get("action_history", []),
        }
        self.sessions.upsert(session_id, str(csv_path), session_payload)

        return 200, {
            "session_id": session_id,
            "csv_path": str(csv_path),
            "schema_version": validation.schema_version,
            "source_type": source_type,
            "source_value": source_value,
        }

    def get_sessions(self) -> tuple[int, dict]:
        sessions = self.sessions.list_sessions()
        return 200, {
            "sessions": [
                {
                    "session_id": s.session_id,
                    "display_name": Path(s.csv_path).name,
                    "csv_path": s.csv_path,
                    "updated_at": s.updated_at.isoformat(),
                }
                for s in sessions
            ]
        }

    def get_session(self, session_id: str) -> tuple[int, dict]:
        state = self.sessions.get(session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"session_id {session_id} not found"}
        return 200, {
            "session_id": state.session_id,
            "csv_path": state.csv_path,
            "updated_at": state.updated_at.isoformat(),
            **(state.payload or {}),
        }

    def patch_thresholds(self, session_id: str, payload: dict[str, Any]) -> tuple[int, dict]:
        state = self.sessions.get(session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"session_id {session_id} not found"}

        session_payload = dict(state.payload or {})
        similarity_threshold = int(payload.get("similarity_threshold", 85))
        recommendation_threshold = int(payload.get("recommendation_threshold", 70))

        thresholds = GroupingThresholds(similarity_threshold=similarity_threshold)
        groups = GroupingService.build_groups(session_payload.get("candidates", []), thresholds)
        scored_groups = RecommendationService.score_groups(
            groups,
            recommendation_threshold=recommendation_threshold,
        )

        session_payload["thresholds"] = {
            "similarity_threshold": similarity_threshold,
            "recommendation_threshold": recommendation_threshold,
        }
        session_payload["groups"] = scored_groups
        self.sessions.upsert(state.session_id, state.csv_path, session_payload)
        self._sidecar.save(Path(state.csv_path), session_payload)

        return 200, {
            "session_id": state.session_id,
            "csv_path": state.csv_path,
            **session_payload,
        }

    def get_scan_directory(self, directory_path: str) -> tuple[int, dict]:
        root = Path(directory_path)
        if not root.exists() or not root.is_dir():
            return 400, {"error": "validation_error", "message": "directory_path must exist"}

        csv_files = sorted(root.glob("*.csv"))
        return 200, {
            "files": [
                {
                    "display_name": p.name,
                    "csv_path": str(p),
                }
                for p in csv_files
            ]
        }
