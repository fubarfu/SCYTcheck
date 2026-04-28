from __future__ import annotations

from src.services.review_service import ReviewService
from src.web.api.routes.settings import SettingsHandler


class ReviewHandler:
    def __init__(
        self,
        review_service: ReviewService | None = None,
        settings_handler: SettingsHandler | None = None,
    ) -> None:
        self.review_service = review_service or ReviewService()
        self.settings_handler = settings_handler or SettingsHandler()

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

        return 200, result
