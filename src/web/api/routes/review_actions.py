from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.web.api.schemas import (
    REVIEW_ACTION_TYPES,
    ReviewActionRequestDTO,
    ReviewActionValidationErrorResponseDTO,
    ReviewValidationFeedbackDTO,
    SchemaValidationError,
)
from src.web.app.group_mutation_service import GroupMutationService
from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.web.app.session_manager import SessionManager
from src.web.app.review_grouping import recompute_groups

VALID_ACTION_TYPES = REVIEW_ACTION_TYPES


class ReviewActionsHandler:
    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self.sessions = session_manager or SessionManager()
        self._sidecar = ReviewSidecarStore()

    def post_action(self, session_id: str, payload: dict[str, Any]) -> tuple[int, dict]:
        state = self.sessions.get(session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"session_id {session_id} not found"}

        try:
            action_request = ReviewActionRequestDTO.from_payload(payload)
        except SchemaValidationError as exc:
            return 400, {"error": "validation_error", "message": str(exc)}

        action_type = action_request.action_type
        target_ids = action_request.target_ids
        action_payload = dict(action_request.payload)
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        action_record = {
            "action_id": action_id,
            "action_type": action_type,
            "target_ids": target_ids,
            "payload": action_payload,
            "applied_at": datetime.now(UTC).isoformat(),
        }

        session_payload = recompute_groups(dict(state.payload or {}))
        if action_type == "toggle_collapse":
            group_id = str(action_payload.get("group_id", "")).strip()
            if group_id:
                requested = action_payload.get("is_collapsed")
                requested_bool = bool(requested) if requested is not None else None
                action_payload["is_collapsed"] = self._sidecar.resolve_group_collapsed_target(
                    session_payload,
                    group_id,
                    requested_bool,
                )
        mutation_payload, validation_payload, handled = GroupMutationService.apply_action(
            session_payload,
            action_type,
            target_ids,
            action_payload,
        )

        if handled:
            if validation_payload and not validation_payload.get("is_valid", False):
                feedback = ReviewValidationFeedbackDTO(
                    is_valid=False,
                    candidate_name=str(validation_payload.get("candidate_name", "")),
                    message=str(validation_payload.get("message", "Validation failed")),
                    conflict_group_id=str(validation_payload.get("conflict_group_id", "")) or None,
                    hint=str(validation_payload.get("hint", "")) or None,
                )
                failure = ReviewActionValidationErrorResponseDTO(
                    error="validation_error",
                    message=feedback.message or "Validation failed",
                    validation=feedback,
                    action_type=action_type,
                    group_id=str(action_payload.get("group_id", "")).strip() or None,
                    candidate_id=(target_ids[0] if target_ids else None),
                )
                return 422, failure.to_payload()
            updated_payload = dict(mutation_payload)
        else:
            candidates: list[dict] = list(session_payload.get("candidates", []))
            candidates = _apply_action(candidates, action_type, target_ids, action_payload)
            updated_payload = {
                **session_payload,
                "candidates": candidates,
            }

        history: list[dict] = list(updated_payload.get("action_history", []))
        history.append(action_record)
        updated_payload["action_history"] = history

        if "accepted_names_original" not in updated_payload:
            updated_payload["accepted_names_original"] = dict(updated_payload.get("accepted_names", {}))
        if "rejected_candidates_original" not in updated_payload:
            updated_payload["rejected_candidates_original"] = dict(updated_payload.get("rejected_candidates", {}))
        if "collapsed_groups_original" not in updated_payload:
            updated_payload["collapsed_groups_original"] = dict(updated_payload.get("collapsed_groups", {}))
        if "resolution_status_original" not in updated_payload:
            updated_payload["resolution_status_original"] = dict(updated_payload.get("resolution_status", {}))

        updated_payload = recompute_groups(updated_payload)
        self.sessions.upsert(state.session_id, state.csv_path, updated_payload)
        self._sidecar.save(Path(state.csv_path), updated_payload)

        return 200, {
            "session_id": session_id,
            "action_id": action_id,
            "persisted": True,
            "updated_at": datetime.now(UTC).isoformat(),
        }

    def post_undo(self, session_id: str) -> tuple[int, dict]:
        state = self.sessions.get(session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"session_id {session_id} not found"}

        session_payload = dict(state.payload or {})
        history: list[dict] = list(session_payload.get("action_history", []))
        if not history:
            return 400, {"error": "no_actions", "message": "No actions to undo"}

        undone = history.pop()
        action_id = undone.get("action_id", "")

        replay_payload: dict[str, Any] = {
            **session_payload,
            "candidates": list(session_payload.get("candidates_original", [])),
            "accepted_names": dict(session_payload.get("accepted_names_original", {})),
            "rejected_candidates": dict(session_payload.get("rejected_candidates_original", {})),
            "collapsed_groups": dict(session_payload.get("collapsed_groups_original", {})),
            "resolution_status": dict(session_payload.get("resolution_status_original", {})),
            "action_history": [],
        }

        for record in history:
            replay_payload = recompute_groups(replay_payload)
            mutated_payload, _, handled = GroupMutationService.apply_action(
                replay_payload,
                record["action_type"],
                record["target_ids"],
                record.get("payload", {}),
            )
            if handled:
                replay_payload = mutated_payload
            else:
                replay_payload["candidates"] = _apply_action(
                    list(replay_payload.get("candidates", [])),
                    record["action_type"],
                    record["target_ids"],
                    record.get("payload", {}),
                )

            replay_history = list(replay_payload.get("action_history", []))
            replay_history.append(record)
            replay_payload["action_history"] = replay_history

        updated_payload: dict[str, Any] = dict(replay_payload)
        updated_payload["action_history"] = history
        updated_payload = recompute_groups(updated_payload)
        self.sessions.upsert(state.session_id, state.csv_path, updated_payload)
        self._sidecar.save(Path(state.csv_path), updated_payload)

        return 200, {
            "session_id": session_id,
            "undone_action_id": action_id,
            "remaining_undo_count": len(history),
        }


def _apply_action(
    candidates: list[dict], action_type: str, target_ids: list[str], action_payload: dict
) -> list[dict]:
    target_set = set(target_ids)
    updated = []
    for c in candidates:
        cid = c.get("candidate_id", "")
        if cid in target_set:
            c = dict(c)
            if action_type == "confirm":
                c["status"] = "confirmed"
            elif action_type == "reject":
                c["status"] = "rejected"
            elif action_type == "edit":
                c["status"] = "confirmed"
                c["corrected_text"] = action_payload.get(
                    "corrected_text", c.get("extracted_name", "")
                )
            elif action_type == "remove":
                continue
        updated.append(c)
    return updated
