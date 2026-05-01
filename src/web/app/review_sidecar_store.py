from __future__ import annotations

import json
import os
import re
from hashlib import sha1
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


class ReviewSidecarStore:
    """Sidecar persistence using atomic rename to avoid torn writes."""

    WORKSPACE_REVIEW_STATE = "review_state.json"

    @staticmethod
    def sidecar_path_for_csv(csv_path: Path | str) -> Path:
        csv_file = Path(csv_path)
        return csv_file.with_suffix(".review.json")

    @classmethod
    def workspace_review_state_path(cls, workspace_root: Path | str) -> Path:
        return Path(workspace_root) / cls.WORKSPACE_REVIEW_STATE

    def resolve_workspace_root(self, csv_path: Path | str) -> Path | None:
        csv_file = Path(csv_path)
        target_csv = str(csv_file.resolve(strict=False))

        # Fast path: CSV already lives inside its workspace folder (sibling of review_state.json)
        if csv_file.parent.parent.name == ".scyt_review_workspaces":
            candidate = self.workspace_review_state_path(csv_file.parent)
            if candidate.exists():
                return csv_file.parent

        workspace_parent = csv_file.parent / ".scyt_review_workspaces"
        if not workspace_parent.exists():
            return None

        for workspace_dir in workspace_parent.iterdir():
            if not workspace_dir.is_dir():
                continue
            review_state_path = self.workspace_review_state_path(workspace_dir)
            if not review_state_path.exists():
                continue
            try:
                payload = json.loads(review_state_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            result_csv_path = str(payload.get("result_csv_path", "")).strip()
            if not result_csv_path:
                continue
            if str(Path(result_csv_path).resolve(strict=False)) == target_csv:
                return workspace_dir
        return None

    def review_state_path_for_csv(self, csv_path: Path | str) -> Path | None:
        workspace_root = self.resolve_workspace_root(csv_path)
        if workspace_root is None:
            return None
        review_state_path = self.workspace_review_state_path(workspace_root)
        return review_state_path if review_state_path.exists() else None

    def load(self, csv_path: Path | str) -> dict[str, Any] | None:
        candidate_paths: list[Path] = []
        # If CSV lives inside its workspace folder, the sibling review_state.json is authoritative
        csv_file = Path(csv_path)
        if csv_file.parent.parent.name == ".scyt_review_workspaces":
            sibling = self.workspace_review_state_path(csv_file.parent)
            if sibling not in candidate_paths:
                candidate_paths.append(sibling)
        workspace_review_state = self.review_state_path_for_csv(csv_path)
        if workspace_review_state is not None and workspace_review_state not in candidate_paths:
            candidate_paths.append(workspace_review_state)
        candidate_paths.append(self.sidecar_path_for_csv(csv_path))

        payload: dict[str, Any] | None = None
        for sidecar_path in candidate_paths:
            if not sidecar_path.exists():
                continue
            with sidecar_path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                payload = loaded
                break

        if not isinstance(payload, dict):
            return None
        return payload

    @staticmethod
    def make_video_id(source_hint: str) -> str:
        """Build a stable, filesystem-safe video identity from a source hint."""
        normalized = re.sub(r"\s+", " ", str(source_hint or "").strip().lower())
        digest = sha1(normalized.encode("utf-8")).hexdigest()[:16]
        return f"vid_{digest}"

    def ensure_workspace_metadata(
        self,
        csv_path: Path | str,
        session_payload: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(session_payload or {})
        csv_file = Path(csv_path)
        source_hint = str(payload.get("source_value") or csv_file.resolve(strict=False))
        workspace = payload.get("workspace")
        if not isinstance(workspace, dict):
            workspace = {}

        video_id = str(workspace.get("video_id", "")).strip() or self.make_video_id(source_hint)
        display_title = str(workspace.get("display_title", "")).strip() or csv_file.stem
        # If the CSV already lives inside a workspace folder (parent is a video_id dir
        # inside .scyt_review_workspaces), reuse that folder rather than double-nesting.
        if csv_file.parent.parent.name == ".scyt_review_workspaces":
            workspace_root = csv_file.parent
        else:
            workspace_root = csv_file.parent / ".scyt_review_workspaces" / video_id
        history_container = workspace_root / "history.json"

        payload["workspace"] = {
            "video_id": video_id,
            "display_title": display_title,
            "workspace_path": str(workspace_root),
            "history_container_path": str(history_container),
        }
        return payload

    def save(self, csv_path: Path | str, session_payload: dict[str, Any]) -> Path:
        payload = self.ensure_workspace_metadata(csv_path, session_payload)
        payload["result_csv_path"] = str(Path(csv_path))
        workspace_root = Path(payload["workspace"]["workspace_path"])
        sidecar_path = self.workspace_review_state_path(workspace_root)
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=sidecar_path.parent,
            encoding="utf-8",
            suffix=".tmp",
        ) as tmp:
            json.dump(payload, tmp, ensure_ascii=True, indent=2)
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

        overrides = payload.get("candidate_group_overrides")
        if not isinstance(overrides, dict):
            payload["candidate_group_overrides"] = {}
        else:
            payload["candidate_group_overrides"] = {
                str(candidate_id): str(group_id)
                for candidate_id, group_id in overrides.items()
                if str(candidate_id).strip() and str(group_id).strip()
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

    def clear_group_collapsed(self, session_payload: dict[str, Any], group_id: str) -> dict[str, Any]:
        payload = self.ensure_group_state_maps(session_payload)
        collapsed = dict(payload["collapsed_groups"])
        collapsed.pop(group_id, None)
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

    def clear_group_resolution_status(self, session_payload: dict[str, Any], group_id: str) -> dict[str, Any]:
        payload = self.ensure_group_state_maps(session_payload)
        statuses = dict(payload["resolution_status"])
        statuses.pop(group_id, None)
        payload["resolution_status"] = statuses
        return payload

    def set_candidate_group_override(
        self,
        session_payload: dict[str, Any],
        candidate_id: str,
        group_id: str,
    ) -> dict[str, Any]:
        payload = self.ensure_group_state_maps(session_payload)
        overrides = dict(payload.get("candidate_group_overrides", {}))
        overrides[str(candidate_id)] = str(group_id)
        payload["candidate_group_overrides"] = overrides
        return payload

    def set_candidates_group_override(
        self,
        session_payload: dict[str, Any],
        candidate_ids: list[str],
        group_id: str,
    ) -> dict[str, Any]:
        payload = self.ensure_group_state_maps(session_payload)
        overrides = dict(payload.get("candidate_group_overrides", {}))
        for candidate_id in candidate_ids:
            cleaned = str(candidate_id).strip()
            if cleaned:
                overrides[cleaned] = str(group_id)
        payload["candidate_group_overrides"] = overrides
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
