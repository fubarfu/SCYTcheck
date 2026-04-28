from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.web.app.review_sidecar_store import ReviewSidecarStore


class ReviewService:
    """Merge review context across runs and persist user actions."""

    def __init__(self, sidecar_store: ReviewSidecarStore | None = None) -> None:
        self.sidecar_store = sidecar_store or ReviewSidecarStore()

    def merge_review_context(self, project_location: str, video_id: str) -> dict[str, Any]:
        workspace_root = Path(project_location) / video_id
        if not workspace_root.exists():
            raise FileNotFoundError(f"video_id {video_id} not found")

        run_sidecars = sorted(workspace_root.glob("result_*.review.json"), key=lambda p: p.name)
        if not run_sidecars:
            review_state_path = workspace_root / "review_state.json"
            if review_state_path.exists():
                run_sidecars = [review_state_path]

        runs: list[dict[str, Any]] = []
        for sidecar_path in run_sidecars:
            try:
                payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(payload, dict):
                runs.append(payload)

        prior_state_path = workspace_root / ".scyt_review_workspaces" / "review_state.json"
        prior_state = self._load_prior_state(prior_state_path)
        prior_decisions = self._extract_prior_decisions(prior_state)

        merged_candidates = self._merge_candidates(runs, prior_decisions)
        merged_candidates = self.mark_new_candidates(merged_candidates, runs, prior_decisions)

        return {
            "video_id": video_id,
            "video_url": self._resolve_video_url(runs, video_id),
            "project_location": str(workspace_root),
            "run_count": len(runs),
            "latest_run_id": str(len(runs) - 1) if runs else "0",
            "candidates": merged_candidates,
            "groups": [],
        }

    def mark_new_candidates(
        self,
        merged_candidates: list[dict[str, Any]],
        runs: list[dict[str, Any]],
        prior_decisions: dict[str, dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        if not runs:
            return merged_candidates

        prior_decisions = prior_decisions or {}

        prior_spellings: set[str] = set()
        latest = runs[-1]
        latest_spellings: set[str] = set()

        for run in runs[:-1]:
            for candidate in list(run.get("candidates") or []):
                spelling = str(candidate.get("extracted_name") or candidate.get("spelling") or "").strip()
                if spelling:
                    prior_spellings.add(spelling)

        for candidate in list(latest.get("candidates") or []):
            spelling = str(candidate.get("extracted_name") or candidate.get("spelling") or "").strip()
            if spelling:
                latest_spellings.add(spelling)

        for candidate in merged_candidates:
            candidate_id = str(candidate.get("id") or "").strip()
            spelling = str(candidate.get("spelling") or "").strip()
            if not spelling:
                candidate["marked_new"] = False
                continue
            is_new = spelling in latest_spellings and spelling not in prior_spellings
            prior = prior_decisions.get(candidate_id)
            if isinstance(prior, dict) and prior.get("marked_new") is False:
                candidate["marked_new"] = False
            else:
                candidate["marked_new"] = is_new

        return merged_candidates

    def apply_candidate_action(
        self,
        project_location: str,
        video_id: str,
        candidate_id: str,
        action: str,
        user_note: str | None = None,
    ) -> dict[str, Any]:
        if action not in {"confirmed", "rejected", "edited", "clear_new"}:
            raise ValueError("Action must be one of: confirmed, rejected, edited, clear_new")

        workspace_root = Path(project_location) / video_id / ".scyt_review_workspaces"
        workspace_root.mkdir(parents=True, exist_ok=True)
        review_state_path = workspace_root / "review_state.json"

        payload = self._load_prior_state(review_state_path)
        decisions = payload.get("candidate_decisions")
        if not isinstance(decisions, dict):
            decisions = {}

        previous = decisions.get(candidate_id)
        if not isinstance(previous, dict):
            previous = {}

        decision = previous.get("decision") if action == "clear_new" else action
        if action == "clear_new" and not decision:
            decision = "unreviewed"

        decisions[candidate_id] = {
            "decision": decision,
            "marked_new": False,
            "user_note": (user_note or "").strip() or previous.get("user_note", ""),
        }
        payload["candidate_decisions"] = decisions

        review_state_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

        return {
            "candidate_id": candidate_id,
            "decision": decisions[candidate_id]["decision"],
            "marked_new": False,
        }

    @staticmethod
    def _load_prior_state(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _extract_prior_decisions(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        decisions = payload.get("candidate_decisions")
        if not isinstance(decisions, dict):
            return {}
        normalized: dict[str, dict[str, Any]] = {}
        for candidate_id, item in decisions.items():
            if isinstance(item, dict):
                normalized[str(candidate_id)] = item
        return normalized

    @staticmethod
    def _merge_candidates(runs: list[dict[str, Any]], prior_decisions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        first_seen: dict[str, str] = {}

        for run_idx, run_payload in enumerate(runs):
            run_id = str(run_idx)
            for candidate in list(run_payload.get("candidates") or []):
                spelling = str(candidate.get("extracted_name") or candidate.get("spelling") or "").strip()
                if not spelling:
                    continue

                candidate_id = str(candidate.get("candidate_id") or f"cand-{spelling.lower()}")
                if spelling not in merged:
                    first_seen[spelling] = run_id
                    merged[spelling] = {
                        "id": candidate_id,
                        "spelling": spelling,
                        "discovered_in_run": run_id,
                        "marked_new": False,
                        "decision": "unreviewed",
                        "frame_count": 0,
                        "frame_samples": [],
                    }

                prior = prior_decisions.get(candidate_id)
                if isinstance(prior, dict):
                    decision = str(prior.get("decision") or "unreviewed")
                    merged[spelling]["decision"] = decision
                    if prior.get("marked_new") is False:
                        merged[spelling]["marked_new"] = False

        for spelling, run_id in first_seen.items():
            merged[spelling]["discovered_in_run"] = run_id

        return list(merged.values())

    @staticmethod
    def _resolve_video_url(runs: list[dict[str, Any]], fallback: str) -> str:
        for run in reversed(runs):
            source_value = str(run.get("source_value") or "").strip()
            if source_value:
                return source_value
        return fallback
