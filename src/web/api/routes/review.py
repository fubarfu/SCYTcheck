from __future__ import annotations

from pathlib import Path
from typing import Any

from src.services.review_service import ReviewService
from src.web.app.review_history_store import ReviewHistoryStore
from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.web.app.session_manager import SessionManager
from src.web.api.routes.settings import SettingsHandler


class ReviewHandler:
    def __init__(
        self,
        review_service: ReviewService | None = None,
        settings_handler: SettingsHandler | None = None,
        session_manager: SessionManager | None = None,
        history_store: ReviewHistoryStore | None = None,
    ) -> None:
        self.review_service = review_service or ReviewService()
        self.settings_handler = settings_handler or SettingsHandler()
        self.sessions = session_manager or SessionManager()
        self.sidecar = ReviewSidecarStore()
        self.history_store = history_store or ReviewHistoryStore(self.sidecar)

    @staticmethod
    def _source_type_from_value(source_value: str) -> str:
        value = source_value.strip().lower()
        if value.startswith("http://") or value.startswith("https://") or "youtube.com" in value or "youtu.be" in value:
            return "youtube_url"
        return "local_file"

    @staticmethod
    def _int_or_zero(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 0
        return max(0, parsed)

    @staticmethod
    def _resolve_workspace_csv_path(workspace_root: Path) -> Path:
        latest = workspace_root / "result_latest.csv"
        if latest.exists():
            return latest

        candidates = sorted(workspace_root.glob("result_*.csv"), key=lambda path: path.name)
        if candidates:
            return candidates[-1]
        return latest

    def _context_to_session_payload(self, context: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
        workspace_root = Path(str(context.get("project_location", "")).strip())
        csv_path = self._resolve_workspace_csv_path(workspace_root)
        video_url = str(context.get("video_url", "")).strip()
        source_type = self._source_type_from_value(video_url)
        run_count = self._int_or_zero(context.get("run_count"))

        groups = [group for group in list(context.get("groups") or []) if isinstance(group, dict)]
        candidates = [candidate for candidate in list(context.get("candidates") or []) if isinstance(candidate, dict)]
        candidate_decision_by_id = {
            str(candidate.get("id") or "").strip(): str(candidate.get("decision") or "unreviewed").strip().lower()
            for candidate in candidates
            if str(candidate.get("id") or "").strip()
        }

        accepted_names: dict[str, str] = {}
        normalized_groups: list[dict[str, Any]] = []
        for group in groups:
            group_id = str(group.get("id") or "").strip()
            if not group_id:
                continue

            decision = str(group.get("decision") or "unreviewed").strip().lower()
            is_resolved = decision == "confirmed"
            group_name = str(group.get("name") or "").strip()
            if is_resolved and group_name:
                accepted_names[group_id] = group_name

            member_ids = [
                str(candidate_id).strip()
                for candidate_id in list(group.get("candidate_ids") or [])
                if str(candidate_id).strip()
            ]
            rejected_candidate_ids = [
                candidate_id
                for candidate_id in member_ids
                if candidate_decision_by_id.get(candidate_id) == "rejected"
            ]

            normalized_groups.append(
                {
                    "group_id": group_id,
                    "resolution_status": "RESOLVED" if is_resolved else "UNRESOLVED",
                    "accepted_name": group_name if is_resolved and group_name else None,
                    "rejected_candidate_ids": rejected_candidate_ids,
                    "candidates": [
                        {
                            "candidate_id": candidate_id,
                            "status": candidate_decision_by_id.get(candidate_id, "unreviewed"),
                        }
                        for candidate_id in member_ids
                    ],
                }
            )

        normalized_candidates = [
            {
                "candidate_id": str(candidate.get("id") or "").strip(),
                "extracted_name": str(candidate.get("spelling") or "").strip(),
                "start_timestamp": str(candidate.get("start_timestamp") or ""),
                "status": str(candidate.get("decision") or "unreviewed").strip().lower(),
                "corrected_text": str(candidate.get("corrected_text") or "").strip() or None,
                "marked_new": bool(candidate.get("marked_new")),
            }
            for candidate in candidates
            if str(candidate.get("id") or "").strip()
        ]

        payload: dict[str, Any] = {
            "source_type": source_type,
            "source_value": video_url,
            "thresholds": dict(context.get("thresholds") or {}),
            "candidates": normalized_candidates,
            "groups": normalized_groups,
            "accepted_names": accepted_names,
            "validation_outcomes": dict(context.get("validation_outcomes") or {}),
            "action_history": [],
            "workspace": {
                "video_id": str(context.get("video_id") or "").strip(),
                "display_title": str(context.get("video_url") or context.get("video_id") or "").strip(),
            },
        }
        payload = self.sidecar.ensure_workspace_metadata(csv_path, payload)
        payload["workspace"]["run_count"] = run_count
        return csv_path, payload

    def _flush_active_video_session_if_switching(self, next_video_id: str) -> None:
        active_state = self.sessions.get_active_session()
        if active_state is None:
            return

        active_payload = self.sidecar.ensure_workspace_metadata(Path(active_state.csv_path), dict(active_state.payload or {}))
        active_video_id = str(active_payload.get("workspace", {}).get("video_id", "")).strip()
        if not active_video_id or active_video_id == next_video_id:
            return

        self.history_store.append_snapshot(Path(active_state.csv_path), active_payload, "video-switch")
        self.sessions.clear_history_pending(active_state.session_id)

    def _sync_video_context_session(self, context: dict[str, Any], *, trigger_merge_snapshot: bool) -> None:
        video_id = str(context.get("video_id", "")).strip()
        if not video_id:
            return

        self._flush_active_video_session_if_switching(video_id)

        existing = self.sessions.get(video_id)
        next_run_count = self._int_or_zero(context.get("run_count"))
        if trigger_merge_snapshot and existing is not None:
            existing_payload_raw = dict(existing.payload or {})
            existing_payload = self.sidecar.ensure_workspace_metadata(Path(existing.csv_path), existing_payload_raw)
            existing_workspace = existing_payload_raw.get("workspace") if isinstance(existing_payload_raw, dict) else {}
            existing_workspace = existing_workspace if isinstance(existing_workspace, dict) else {}
            existing_run_count = self._int_or_zero(existing_workspace.get("run_count"))
            if next_run_count > existing_run_count:
                self.history_store.append_snapshot(Path(existing.csv_path), existing_payload, "analysis-merge")
                self.sessions.clear_history_pending(existing.session_id)

        csv_path, session_payload = self._context_to_session_payload(context)
        self.sessions.upsert(video_id, str(csv_path), session_payload)

    def get_review_context(self, query: dict[str, str] | None = None) -> tuple[int, dict]:
        """Load merged review context for one video_id from the configured project location."""
        params = query or {}
        video_id = str(params.get("video_id", "")).strip()
        if not video_id:
            return 400, {"error": "validation_error", "message": "video_id is required"}

        settings = self.settings_handler.get_settings()
        project_location = str(settings.get("project_location", "")).strip()

        try:
            payload = self.review_service.merge_review_context(project_location, video_id)
        except FileNotFoundError:
            return 404, {"error": "video_not_found", "message": f"Video with ID {video_id} not found."}

        self._sync_video_context_session(payload, trigger_merge_snapshot=True)

        return 200, payload

    def put_review_action(self, payload: dict[str, str]) -> tuple[int, dict]:
        """Apply a review action to a candidate and persist the resulting decision state."""
        video_id = str(payload.get("video_id", "")).strip()
        candidate_id = str(payload.get("candidate_id", "")).strip()
        action = str(payload.get("action", "")).strip()
        user_note = str(payload.get("user_note", "")).strip() or None

        if not video_id or not candidate_id or not action:
            return 400, {
                "error": "validation_error",
                "message": "video_id, candidate_id, and action are required",
            }

        settings = self.settings_handler.get_settings()
        project_location = str(settings.get("project_location", "")).strip()

        try:
            result = self.review_service.apply_candidate_action(
                project_location=project_location,
                video_id=video_id,
                candidate_id=candidate_id,
                action=action,
                user_note=user_note,
            )
        except ValueError as exc:
            return 400, {"error": "invalid_action", "message": str(exc)}

        try:
            context = self.review_service.merge_review_context(project_location, video_id)
            self._sync_video_context_session(context, trigger_merge_snapshot=False)
            self.sessions.mark_history_pending(video_id)
        except FileNotFoundError:
            pass

        return 200, result

    def put_review_grouping(self, payload: dict[str, object]) -> tuple[int, dict]:
        """Persist grouping settings and recalculate merged groups for video-context review."""
        video_id = str(payload.get("video_id", "")).strip()
        if not video_id:
            return 400, {"error": "validation_error", "message": "video_id is required"}

        thresholds = {
            "similarity_threshold": payload.get("similarity_threshold", 80),
            "recommendation_threshold": payload.get("recommendation_threshold", 70),
            "spelling_influence": payload.get("spelling_influence", 50),
            "temporal_influence": payload.get("temporal_influence", 50),
        }
        reset_decisions = bool(payload.get("reset_decisions", False))

        settings = self.settings_handler.get_settings()
        project_location = str(settings.get("project_location", "")).strip()

        try:
            result = self.review_service.update_grouping_settings(
                project_location=project_location,
                video_id=video_id,
                thresholds=thresholds,
                reset_decisions=reset_decisions,
            )
        except FileNotFoundError:
            return 404, {"error": "video_not_found", "message": f"Video with ID {video_id} not found."}

        self._sync_video_context_session(result, trigger_merge_snapshot=False)
        self.sessions.mark_history_pending(video_id)

        return 200, result
