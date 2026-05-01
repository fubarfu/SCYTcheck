from __future__ import annotations

import csv
import uuid
from pathlib import Path
from typing import Any

from src.web.app.review_grouping import recompute_groups
from src.web.app.result_schema_validator import ResultSchemaValidator
from src.web.app.review_history_store import ReviewHistoryStore
from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.web.app.session_manager import SessionManager
from src.web.api.schemas import ReviewGroupResponseDTO, ReviewLoadRequestDTO, SchemaValidationError


class ReviewSessionHandler:
    """HTTP-style handler for review session load/list/get endpoints."""

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        validator: ResultSchemaValidator | None = None,
        history_store: ReviewHistoryStore | None = None,
    ) -> None:
        self.sessions = session_manager or SessionManager()
        self.validator = validator or ResultSchemaValidator()
        self._sidecar = ReviewSidecarStore()
        self._history = history_store or ReviewHistoryStore(self._sidecar)

    def _flush_session_history(self, state, trigger_type: str, *, force: bool = False) -> str | None:
        if not force and not state.has_pending_history:
            return None
        payload = self._sidecar.ensure_workspace_metadata(Path(state.csv_path), dict(state.payload or {}))
        if force:
            entry = self._history.append_snapshot(Path(state.csv_path), payload, trigger_type)
        else:
            entry = self._history.append_snapshot_if_changed(Path(state.csv_path), payload, trigger_type)
        self.sessions.clear_history_pending(state.session_id)
        if entry is None:
            return None
        return str(entry.get("entry_id", "")) or None

    def _flush_active_session_history_if_switching(
        self,
        next_video_id: str,
        next_session_id: str | None = None,
        *,
        force: bool = False,
    ) -> str | None:
        active_state = self.sessions.get_active_session()
        if active_state is None:
            return None
        if next_session_id and active_state.session_id == next_session_id:
            return None
        active_payload = self._sidecar.ensure_workspace_metadata(Path(active_state.csv_path), dict(active_state.payload or {}))
        active_video_id = str(active_payload.get("workspace", {}).get("video_id", "")).strip()
        if active_video_id == next_video_id:
            return None
        return self._flush_session_history(active_state, "video-switch", force=force)

    def flush_all_pending_history(self, trigger_type: str = "app-close") -> int:
        flushed = 0
        for state in self.sessions.list_sessions():
            if self._flush_session_history(state, trigger_type):
                flushed += 1
        return flushed

    def post_flush_on_close(self, session_id: str) -> tuple[int, dict]:
        state = self.sessions.get(session_id)
        if state is None:
            return 200, {
                "session_id": session_id,
                "flushed": False,
                "history_entry_id": None,
                "reason": "session_not_found",
            }
        payload = self._sidecar.ensure_workspace_metadata(Path(state.csv_path), dict(state.payload or {}))
        entry = self._history.append_snapshot(Path(state.csv_path), payload, "browser-close")
        self.sessions.clear_history_pending(state.session_id)
        return 200, {
            "session_id": session_id,
            "flushed": True,
            "history_entry_id": str(entry.get("entry_id", "")),
            "reason": "flushed",
        }

    def post_load(self, payload: dict[str, Any]) -> tuple[int, dict]:
        try:
            request_dto = ReviewLoadRequestDTO.from_payload(payload)
        except SchemaValidationError as exc:
            return 400, {"error": "validation_error", "message": str(exc)}

        csv_path = request_dto.csv_path
        if not csv_path.exists():
            return 404, {"error": "not_found", "message": f"File not found: {csv_path}"}

        validation = self.validator.validate(csv_path)
        if not validation.is_valid:
            return 422, {
                "error": "invalid_schema",
                "message": validation.error or "Unsupported schema version",
                "schema_version": validation.schema_version,
                "missing_columns": validation.missing_columns,
            }

        session_id = f"sess_{csv_path.stem}_{uuid.uuid4().hex[:8]}"
        existing = ReviewSidecarStore.ensure_group_state_maps(self._sidecar.load(csv_path) or {})
        source_type = existing.get("source_type", "local_file")
        source_value = existing.get("source_value", "")
        candidates = existing.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            candidates = self._load_candidates_from_csv(csv_path)

        session_payload: dict[str, Any] = {
            "schema_version": validation.schema_version,
            "source_type": source_type,
            "source_value": source_value,
            "candidates": candidates,
            "candidates_original": existing.get("candidates_original", [dict(item) for item in candidates]),
            "action_history": existing.get("action_history", []),
            "validation_outcomes": existing.get("validation_outcomes", {}),
            "validation_queue_size": existing.get("validation_queue_size", 0),
            "review_ready": existing.get("review_ready", False),
            "thresholds": existing.get(
                "thresholds",
                {
                    "similarity_threshold": 80,
                    "recommendation_threshold": 70,
                    "temporal_window_seconds": 2.0,
                    "spelling_influence": 50,
                    "temporal_influence": 50,
                },
            ),
            "accepted_names": existing.get("accepted_names", {}),
            "rejected_candidates": existing.get("rejected_candidates", {}),
            "collapsed_groups": existing.get("collapsed_groups", {}),
            "resolution_status": existing.get("resolution_status", {}),
            "candidate_group_overrides": existing.get("candidate_group_overrides", {}),
            "accepted_names_original": existing.get("accepted_names_original", existing.get("accepted_names", {})),
            "rejected_candidates_original": existing.get("rejected_candidates_original", existing.get("rejected_candidates", {})),
            "collapsed_groups_original": existing.get("collapsed_groups_original", existing.get("collapsed_groups", {})),
            "resolution_status_original": existing.get("resolution_status_original", existing.get("resolution_status", {})),
            "candidate_group_overrides_original": existing.get(
                "candidate_group_overrides_original",
                existing.get("candidate_group_overrides", {}),
            ),
        }
        session_payload = recompute_groups(session_payload)
        session_payload = self._sidecar.ensure_workspace_metadata(csv_path, session_payload)
        self._flush_active_session_history_if_switching(session_payload["workspace"]["video_id"], force=True)
        self.sessions.upsert(session_id, str(csv_path), session_payload)
        self._sidecar.save(csv_path, session_payload)

        return 200, {
            "session_id": session_id,
            "csv_path": str(csv_path),
            "schema_version": validation.schema_version,
            "source_type": source_type,
            "source_value": source_value,
            "workspace": dict(session_payload["workspace"]),
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
        current_payload = self._sidecar.ensure_workspace_metadata(Path(state.csv_path), dict(state.payload or {}))
        self._flush_active_session_history_if_switching(current_payload["workspace"]["video_id"], next_session_id=session_id)
        refreshed_payload = recompute_groups(current_payload)
        refreshed_payload = self._sidecar.ensure_workspace_metadata(Path(state.csv_path), refreshed_payload)
        response_payload = dict(refreshed_payload)
        response_payload["groups"] = _serialize_groups_for_session(list(refreshed_payload.get("groups", [])))
        self.sessions.upsert(state.session_id, state.csv_path, refreshed_payload)
        return 200, {
            "session_id": state.session_id,
            "csv_path": state.csv_path,
            "updated_at": state.updated_at.isoformat(),
            **response_payload,
        }

    def patch_thresholds(self, session_id: str, payload: dict[str, Any]) -> tuple[int, dict]:
        state = self.sessions.get(session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"session_id {session_id} not found"}

        session_payload = dict(state.payload or {})
        existing_thresholds = dict(session_payload.get("thresholds", {}))

        similarity_threshold = int(payload.get("similarity_threshold", existing_thresholds.get("similarity_threshold", 85)))
        recommendation_threshold = int(payload.get("recommendation_threshold", existing_thresholds.get("recommendation_threshold", 70)))
        temporal_window_seconds = float(payload.get("temporal_window_seconds", existing_thresholds.get("temporal_window_seconds", 2.0)))
        spelling_influence = int(payload.get("spelling_influence", existing_thresholds.get("spelling_influence", 50)))
        temporal_influence = int(payload.get("temporal_influence", existing_thresholds.get("temporal_influence", 50)))

        session_payload["thresholds"] = {
            "similarity_threshold": similarity_threshold,
            "recommendation_threshold": recommendation_threshold,
            "temporal_window_seconds": temporal_window_seconds,
            "spelling_influence": spelling_influence,
            "temporal_influence": temporal_influence,
        }
        session_payload = recompute_groups(session_payload)
        session_payload = self._sidecar.ensure_workspace_metadata(Path(state.csv_path), session_payload)
        self.sessions.upsert(state.session_id, state.csv_path, session_payload)
        self.sessions.mark_history_pending(state.session_id)
        self._sidecar.save(Path(state.csv_path), session_payload)

        return 200, {
            "session_id": state.session_id,
            "csv_path": state.csv_path,
            **session_payload,
        }

    def post_recalculate(self, session_id: str) -> tuple[int, dict]:
        state = self.sessions.get(session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"session_id {session_id} not found"}

        session_payload = dict(state.payload or {})
        current_candidates = list(session_payload.get("candidates", []))

        reset_candidates: list[dict[str, Any]] = []
        for raw_candidate in current_candidates:
            candidate = dict(raw_candidate)
            candidate["status"] = "pending"
            candidate.pop("corrected_text", None)
            reset_candidates.append(candidate)

        session_payload["candidates"] = reset_candidates
        session_payload["candidates_original"] = [dict(candidate) for candidate in reset_candidates]
        session_payload["accepted_names"] = {}
        session_payload["rejected_candidates"] = {}
        session_payload["collapsed_groups"] = {}
        session_payload["resolution_status"] = {}
        session_payload["candidate_group_overrides"] = {}
        session_payload["action_history"] = []

        session_payload["accepted_names_original"] = {}
        session_payload["rejected_candidates_original"] = {}
        session_payload["collapsed_groups_original"] = {}
        session_payload["resolution_status_original"] = {}
        session_payload["candidate_group_overrides_original"] = {}

        session_payload = recompute_groups(session_payload)
        session_payload = self._sidecar.ensure_workspace_metadata(Path(state.csv_path), session_payload)
        self.sessions.upsert(state.session_id, state.csv_path, session_payload)
        self.sessions.mark_history_pending(state.session_id)
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

    @staticmethod
    def _load_candidates_from_csv(csv_path: Path) -> list[dict[str, Any]]:
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            rows = [row for row in reader if row]

        if not rows:
            return []

        header_row = rows[0]
        data_rows = rows[1:]
        if header_row and header_row[0].startswith("#schema_version="):
            if len(rows) < 2:
                return []
            header_row = rows[1]
            data_rows = rows[2:]

        header_index = {name: idx for idx, name in enumerate(header_row)}
        name_idx = header_index.get("PlayerName")
        time_idx = header_index.get("StartTimestamp")
        if name_idx is None or time_idx is None:
            return []

        candidates: list[dict[str, Any]] = []
        for index, row in enumerate(data_rows, start=1):
            if len(row) <= max(name_idx, time_idx):
                continue
            extracted_name = str(row[name_idx]).strip()
            start_timestamp = str(row[time_idx]).strip()
            if not extracted_name:
                continue
            candidates.append(
                {
                    "candidate_id": f"csv_{index}",
                    "extracted_name": extracted_name,
                    "start_timestamp": start_timestamp,
                    "status": "pending",
                }
            )

        return candidates


def _serialize_groups_for_session(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for group in groups:
        payload = dict(group)
        payload.setdefault("accepted_name_summary", payload.get("accepted_name"))
        payload.setdefault("occurrence_count", int(payload.get("total_candidate_count", len(payload.get("candidates", [])))))
        payload.setdefault("has_conflicting_spellings", len(payload.get("active_spellings", [])) > 1)
        payload.setdefault("conflict_spelling_count", len(payload.get("active_spellings", [])))
        payload.setdefault("remembered_is_collapsed", payload.get("is_collapsed") if "is_collapsed" in payload else None)
        dto = ReviewGroupResponseDTO.from_payload(payload)
        normalized = dict(group)
        normalized.update(dto.to_payload())
        normalized["has_conflicting_spellings"] = bool(payload.get("has_conflicting_spellings", False))
        normalized["conflict_spelling_count"] = int(payload.get("conflict_spelling_count", 0))
        normalized["remembered_is_collapsed"] = payload.get("remembered_is_collapsed")
        serialized.append(normalized)
    return serialized
