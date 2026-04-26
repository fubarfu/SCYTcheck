from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


class ReviewSidecarStore:
    """Sidecar persistence using atomic rename to avoid torn writes."""

    @staticmethod
    def sidecar_path_for_csv(csv_path: Path | str) -> Path:
        csv_file = Path(csv_path)
        return csv_file.with_suffix(".review.json")

    def load(self, csv_path: Path | str) -> dict[str, Any] | None:
        sidecar_path = self.sidecar_path_for_csv(csv_path)
        if not sidecar_path.exists():
            return None
        with sidecar_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            return None
        return payload

    def save(self, csv_path: Path | str, session_payload: dict[str, Any]) -> Path:
        sidecar_path = self.sidecar_path_for_csv(csv_path)
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=sidecar_path.parent,
            encoding="utf-8",
            suffix=".tmp",
        ) as tmp:
            json.dump(session_payload, tmp, ensure_ascii=True, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_path = Path(tmp.name)

        os.replace(temp_path, sidecar_path)
        return sidecar_path

    @staticmethod
    def ensure_group_state_maps(session_payload: dict[str, Any]) -> dict[str, Any]:
        """Guarantee review-group persistence maps exist and are normalized."""
        payload = dict(session_payload or {})

        accepted = payload.get("accepted_names")
        payload["accepted_names"] = dict(accepted) if isinstance(accepted, dict) else {}

        rejected = payload.get("rejected_candidates")
        if not isinstance(rejected, dict):
            payload["rejected_candidates"] = {}
        else:
            payload["rejected_candidates"] = {
                str(group_id): [str(candidate_id) for candidate_id in candidate_ids if str(candidate_id)]
                for group_id, candidate_ids in rejected.items()
                if isinstance(candidate_ids, list)
            }

        collapsed = payload.get("collapsed_groups")
        if not isinstance(collapsed, dict):
            payload["collapsed_groups"] = {}
        else:
            payload["collapsed_groups"] = {
                str(group_id): bool(is_collapsed)
                for group_id, is_collapsed in collapsed.items()
            }

        if not payload["collapsed_groups"]:
            fallback_collapsed: dict[str, bool] = {}
            for group in list(payload.get("groups", [])):
                if not isinstance(group, dict):
                    continue
                group_id = str(group.get("group_id", "")).strip()
                if not group_id:
                    continue
                if "is_collapsed" not in group:
                    continue
                fallback_collapsed[group_id] = bool(group.get("is_collapsed"))
            if fallback_collapsed:
                payload["collapsed_groups"] = fallback_collapsed

        status = payload.get("resolution_status")
        if not isinstance(status, dict):
            payload["resolution_status"] = {}
        else:
            payload["resolution_status"] = {
                str(group_id): str(value)
                for group_id, value in status.items()
            }

        return payload

    def set_group_accepted_name(
        self,
        session_payload: dict[str, Any],
        group_id: str,
        accepted_name: str | None,
    ) -> dict[str, Any]:
        payload = self.ensure_group_state_maps(session_payload)
        accepted = dict(payload["accepted_names"])
        cleaned = (accepted_name or "").strip()
        if cleaned:
            accepted[group_id] = cleaned
        else:
            accepted.pop(group_id, None)
        payload["accepted_names"] = accepted
        return payload

    def set_group_consensus(
        self,
        session_payload: dict[str, Any],
        group_id: str,
        accepted_name: str,
    ) -> dict[str, Any]:
        """Persist accepted name and collapsed resolved state as one atomic mutation."""
        payload = self.set_group_accepted_name(session_payload, group_id, accepted_name)
        payload = self.set_group_resolution_status(payload, group_id, "RESOLVED")
        payload = self.set_group_collapsed(payload, group_id, True)
        return payload

    def set_candidate_rejected(
        self,
        session_payload: dict[str, Any],
        group_id: str,
        candidate_id: str,
        rejected: bool,
    ) -> dict[str, Any]:
        payload = self.ensure_group_state_maps(session_payload)
        rejected_map = dict(payload["rejected_candidates"])
        existing = list(rejected_map.get(group_id, []))
        if rejected:
            if candidate_id not in existing:
                existing.append(candidate_id)
            rejected_map[group_id] = existing
        else:
            filtered = [item for item in existing if item != candidate_id]
            if filtered:
                rejected_map[group_id] = filtered
            else:
                rejected_map.pop(group_id, None)
        payload["rejected_candidates"] = rejected_map
        return payload

    def set_group_collapsed(
        self,
        session_payload: dict[str, Any],
        group_id: str,
        is_collapsed: bool,
    ) -> dict[str, Any]:
        payload = self.ensure_group_state_maps(session_payload)
        collapsed = dict(payload["collapsed_groups"])
        collapsed[group_id] = bool(is_collapsed)
        payload["collapsed_groups"] = collapsed
        return payload

    def set_group_resolution_status(
        self,
        session_payload: dict[str, Any],
        group_id: str,
        resolution_status: str,
    ) -> dict[str, Any]:
        payload = self.ensure_group_state_maps(session_payload)
        statuses = dict(payload["resolution_status"])
        statuses[group_id] = resolution_status
        payload["resolution_status"] = statuses
        return payload

    def resolve_group_collapsed_target(
        self,
        session_payload: dict[str, Any],
        group_id: str,
        requested_is_collapsed: bool | None,
    ) -> bool:
        payload = self.ensure_group_state_maps(session_payload)
        if requested_is_collapsed is not None:
            return bool(requested_is_collapsed)

        collapsed_map = dict(payload.get("collapsed_groups", {}))
        if group_id in collapsed_map:
            return not bool(collapsed_map[group_id])

        for group in list(payload.get("groups", [])):
            if str(group.get("group_id", "")).strip() != group_id:
                continue
            if "is_collapsed" in group:
                return not bool(group.get("is_collapsed"))
            break

        status_map = dict(payload.get("resolution_status", {}))
        status = str(status_map.get(group_id, "UNRESOLVED"))
        # Match hydration defaults when no explicit state has been persisted yet.
        return status == "UNRESOLVED"

    def get_group_state(self, session_payload: dict[str, Any], group_id: str) -> dict[str, Any]:
        payload = self.ensure_group_state_maps(session_payload)
        return {
            "accepted_name": payload["accepted_names"].get(group_id),
            "rejected_candidate_ids": list(payload["rejected_candidates"].get(group_id, [])),
            "is_collapsed": bool(payload["collapsed_groups"].get(group_id, False)),
            "resolution_status": payload["resolution_status"].get(group_id, "UNRESOLVED"),
        }
