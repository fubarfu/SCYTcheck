from __future__ import annotations

import csv
from pathlib import Path

from src.web.app.group_mutation_service import GroupMutationService
from src.web.app.review_grouping import recompute_groups
from src.web.app.session_manager import SessionManager


class ReviewExportHandler:
    """HTTP-style handler for export of deduplicated names and occurrences CSVs."""

    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self.sessions = session_manager or SessionManager()

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
