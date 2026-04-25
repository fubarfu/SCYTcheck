from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.web.app.review_sidecar_store import ReviewSidecarStore
from src.web.app.session_manager import SessionManager
from src.web.app.review_grouping import recompute_groups

VALID_ACTION_TYPES = frozenset(
    {
        "confirm",
        "reject",
        "edit",
        "remove",
        "move_candidate",
        "merge_groups",
        "reorder_group",
    }
)


class ReviewActionsHandler:
    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self.sessions = session_manager or SessionManager()
        self._sidecar = ReviewSidecarStore()

    def post_action(self, session_id: str, payload: dict[str, Any]) -> tuple[int, dict]:
        state = self.sessions.get(session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"session_id {session_id} not found"}

        action_type = str(payload.get("action_type", "")).strip()
        if action_type not in VALID_ACTION_TYPES:
            return 400, {
                "error": "validation_error",
                "message": f"action_type must be one of: {', '.join(sorted(VALID_ACTION_TYPES))}",
            }

        target_ids: list[str] = payload.get("target_ids", [])
        if not isinstance(target_ids, list) or not target_ids:
            return 400, {
                "error": "validation_error",
                "message": "target_ids must be a non-empty list",
            }

        action_payload = payload.get("payload", {})
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        action_record = {
            "action_id": action_id,
            "action_type": action_type,
            "target_ids": target_ids,
            "payload": action_payload,
            "applied_at": datetime.now(UTC).isoformat(),
        }

        session_payload = dict(state.payload or {})
        history: list[dict] = list(session_payload.get("action_history", []))
        history.append(action_record)

        candidates: list[dict] = list(session_payload.get("candidates", []))
        candidates = _apply_action(candidates, action_type, target_ids, action_payload)

        updated_payload: dict[str, Any] = {
            **session_payload,
            "candidates": candidates,
            "action_history": history,
        }
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

        base_candidates: list[dict] = list(session_payload.get("candidates_original", []))
        candidates = base_candidates[:]
        for record in history:
            candidates = _apply_action(
                candidates, record["action_type"], record["target_ids"], record.get("payload", {})
            )

        updated_payload: dict[str, Any] = {
            **session_payload,
            "candidates": candidates,
            "action_history": history,
        }
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
