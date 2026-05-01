from __future__ import annotations

import csv
from pathlib import Path

from src.services.review_service import ReviewService
from src.web.app.group_mutation_service import GroupMutationService
from src.web.app.review_grouping import recompute_groups
from src.web.app.session_manager import SessionManager
from src.web.api.routes.settings import SettingsHandler


def _is_group_resolved(group: dict) -> bool:
    """Best-effort resolved detection across legacy and current payload shapes."""
    resolution_status = str(group.get("resolution_status", "")).strip().upper()
    if resolution_status == "RESOLVED":
        return True

    decision = str(group.get("decision", "")).strip().lower()
    if decision in {"confirmed", "resolved"}:
        return True

    accepted_name = str(group.get("accepted_name") or "").strip()
    accepted_summary = str(group.get("accepted_name_summary") or "").strip()
    return bool(accepted_name or accepted_summary)


class ReviewExportHandler:
    """HTTP-style handler for export of deduplicated names and occurrences CSVs."""

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        review_service: ReviewService | None = None,
        settings_handler: SettingsHandler | None = None,
    ) -> None:
        self.sessions = session_manager or SessionManager()
        self.review_service = review_service or ReviewService()
        self.settings_handler = settings_handler or SettingsHandler()

    @staticmethod
    def _groups_from_context_payload(context_payload: dict) -> list[dict]:
        groups: list[dict] = []
        for raw_group in list(context_payload.get("groups") or []):
            if not isinstance(raw_group, dict):
                continue
            group_id = str(raw_group.get("id") or "").strip()
            if not group_id:
                continue

            decision = str(raw_group.get("decision") or "").strip().lower()
            group_name = str(raw_group.get("name") or "").strip()
            groups.append(
                {
                    "group_id": group_id,
                    "resolution_status": "RESOLVED" if decision == "confirmed" else "UNRESOLVED",
                    "accepted_name": group_name if decision == "confirmed" else "",
                    "accepted_name_summary": group_name if decision == "confirmed" else "",
                    "display_name": group_name or group_id,
                    "decision": decision,
                }
            )
        return groups

    def post_export(self, session_id: str) -> tuple[int, dict]:
        state = self.sessions.get(session_id)
        if state is None:
            return 404, {"error": "not_found", "message": f"session_id {session_id} not found"}

        session_payload = recompute_groups(dict(state.payload or {}))
        gate = GroupMutationService.evaluate_completion_gate(session_payload)
        if not gate["is_complete"]:
            return 422, {
                "error": "completion_gate_failed",
                "message": "Review cannot be exported until all groups are resolved and accepted names are unique",
                "details": {
                    "unresolved_group_ids": gate["unresolved_group_ids"],
                    "duplicate_name_conflicts": gate["duplicate_name_conflicts"],
                },
            }

        candidates: list[dict] = session_payload.get("candidates", [])
        confirmed = [c for c in candidates if c.get("status") in {"confirmed", None}]

        csv_path = Path(state.csv_path)
        names_csv = csv_path.with_suffix(".names.csv")
        occurrences_csv = csv_path.with_suffix(".occurrences.csv")

        # Deduplicated names
        seen_names: dict[str, list[dict]] = {}
        for c in confirmed:
            name = c.get("corrected_text") or c.get("extracted_name", "")
            if name:
                seen_names.setdefault(name, []).append(c)

        with names_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["PlayerName", "OccurrenceCount"])
            for name, occurrences in sorted(seen_names.items()):
                writer.writerow([name, len(occurrences)])

        # Occurrences
        with occurrences_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["PlayerName", "StartTimestamp", "CandidateId"])
            for c in confirmed:
                name = c.get("corrected_text") or c.get("extracted_name", "")
                writer.writerow([name, c.get("start_timestamp", ""), c.get("candidate_id", "")])

        return 200, {
            "session_id": session_id,
            "deduplicated_names_csv_path": str(names_csv),
            "occurrences_csv_path": str(occurrences_csv),
            "confirmed_count": len(confirmed),
            "deduplicated_count": len(seen_names),
        }

    def post_export_names(self, session_id: str, payload: dict | None = None) -> tuple[int, dict]:
        """Export resolved group names only to a caller-provided CSV path."""
        state = self.sessions.get(session_id)

        request_payload = dict(payload or {})
        csv_path_raw = str(request_payload.get("csv_path", "")).strip()
        if not csv_path_raw:
            return 400, {"error": "validation_error", "message": "csv_path is required"}

        csv_path = Path(csv_path_raw)
        if csv_path.suffix.lower() != ".csv":
            return 400, {"error": "validation_error", "message": "csv_path must point to a .csv file"}

        groups: list[dict] = []
        if state is not None:
            session_payload = dict(state.payload or {})
            groups = list(session_payload.get("groups") or [])
            if not groups:
                # Fallback for legacy payloads that don't persist precomputed groups.
                session_payload = recompute_groups(dict(state.payload or {}))
                groups = list(session_payload.get("groups") or [])
        else:
            # In project-video review mode, session_id can be a video_id without an in-memory session.
            settings = self.settings_handler.get_settings()
            project_location = str(settings.get("project_location", "")).strip()
            try:
                context = self.review_service.merge_review_context(project_location, session_id)
            except FileNotFoundError:
                return 404, {"error": "not_found", "message": f"session_id {session_id} not found"}
            groups = self._groups_from_context_payload(context)

        selected_group_ids_raw = request_payload.get("selected_group_ids")
        selected_group_ids: set[str] | None = None
        if isinstance(selected_group_ids_raw, list):
            normalized_ids = {str(item).strip() for item in selected_group_ids_raw if str(item).strip()}
            selected_group_ids = normalized_ids if normalized_ids else None

        rows: list[str] = []
        for group in groups:
            group_id = str(group.get("group_id", "")).strip()
            if selected_group_ids is not None and group_id not in selected_group_ids:
                continue

            is_resolved = _is_group_resolved(group)
            if not is_resolved:
                continue

            group_name = str(
                group.get("accepted_name_summary")
                or group.get("accepted_name")
                or group.get("display_name")
                or group_id
            ).strip()
            if not group_name:
                continue

            rows.append(group_name)

        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for name in rows:
                writer.writerow([name])

        return 200, {
            "session_id": session_id,
            "csv_path": str(csv_path),
            "exported_count": len(rows),
        }
