from __future__ import annotations

from typing import Any

from src.web.app.review_sidecar_store import ReviewSidecarStore


def _candidate_name(candidate: dict[str, Any]) -> str:
  corrected = str(candidate.get("corrected_text", "")).strip()
  if corrected:
    return corrected
  return str(candidate.get("extracted_name", "")).strip()


def _set_candidate_status(candidates: list[dict[str, Any]], candidate_id: str, status: str) -> list[dict[str, Any]]:
  updated: list[dict[str, Any]] = []
  for candidate in candidates:
    item = dict(candidate)
    if str(item.get("candidate_id", "")).strip() == candidate_id:
      item["status"] = status
    updated.append(item)
  return updated


def _set_group_candidate_statuses(
  candidates: list[dict[str, Any]],
  group: dict[str, Any],
  rejected_candidate_ids: set[str],
  confirmed_candidate_id: str | None,
) -> list[dict[str, Any]]:
  group_candidate_ids = {
    str(item.get("candidate_id", "")).strip()
    for item in list(group.get("candidates", []))
    if str(item.get("candidate_id", "")).strip()
  }
  if not group_candidate_ids:
    return list(candidates)

  updated: list[dict[str, Any]] = []
  for candidate in candidates:
    item = dict(candidate)
    candidate_id = str(item.get("candidate_id", "")).strip()
    if candidate_id in group_candidate_ids:
      if candidate_id in rejected_candidate_ids:
        item["status"] = "rejected"
      elif confirmed_candidate_id and candidate_id == confirmed_candidate_id:
        item["status"] = "confirmed"
      else:
        item["status"] = "pending"
    updated.append(item)
  return updated


def _find_group(groups: list[dict[str, Any]], group_id: str) -> dict[str, Any] | None:
  return next((group for group in groups if str(group.get("group_id", "")) == group_id), None)


def _find_group_for_candidate(groups: list[dict[str, Any]], candidate_id: str) -> str | None:
  for group in groups:
    for candidate in list(group.get("candidates", [])):
      if str(candidate.get("candidate_id", "")).strip() == candidate_id:
        return str(group.get("group_id", "")).strip()
  return None


def _find_candidate(group: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
  for candidate in list(group.get("candidates", [])):
    if str(candidate.get("candidate_id", "")).strip() == candidate_id:
      return candidate
  return None


def _active_spellings(group: dict[str, Any], rejected_candidate_ids: set[str]) -> list[str]:
  spellings: set[str] = set()
  for candidate in list(group.get("candidates", [])):
    candidate_id = str(candidate.get("candidate_id", "")).strip()
    if candidate_id in rejected_candidate_ids:
      continue
    candidate_name = _candidate_name(candidate)
    if candidate_name:
      spellings.add(candidate_name)
  return sorted(spellings)


def _duplicate_conflict(
  accepted_names: dict[str, str],
  candidate_name: str,
  *,
  excluded_group_id: str,
) -> str | None:
  normalized_target = candidate_name.strip().lower()
  if not normalized_target:
    return None
  for group_id, accepted_name in accepted_names.items():
    if group_id == excluded_group_id:
      continue
    if str(accepted_name).strip().lower() == normalized_target:
      return group_id
  return None


def _accepted_name_lookup(session_payload: dict[str, Any]) -> dict[str, str]:
  accepted_lookup: dict[str, str] = {
    str(group_id).strip(): str(accepted_name).strip()
    for group_id, accepted_name in dict(session_payload.get("accepted_names", {})).items()
    if str(group_id).strip() and str(accepted_name).strip()
  }

  rejected_map = {
    str(group_id).strip(): {
      str(candidate_id).strip()
      for candidate_id in candidate_ids
      if str(candidate_id).strip()
    }
    for group_id, candidate_ids in dict(session_payload.get("rejected_candidates", {})).items()
    if isinstance(candidate_ids, list)
  }

  for group in list(session_payload.get("groups", [])):
    group_id = str(group.get("group_id", "")).strip()
    if not group_id:
      continue

    explicit_accepted = str(group.get("accepted_name", "")).strip()
    if explicit_accepted:
      accepted_lookup[group_id] = explicit_accepted
      continue

    active_spellings = _active_spellings(group, rejected_map.get(group_id, set()))
    if len(active_spellings) == 1:
      accepted_lookup.setdefault(group_id, active_spellings[0])

  return accepted_lookup


def _validation_payload(
  *,
  is_valid: bool,
  candidate_name: str,
  conflict_group_id: str | None = None,
) -> dict[str, Any]:
  payload: dict[str, Any] = {
    "is_valid": is_valid,
    "candidate_name": candidate_name,
  }
  if not is_valid:
    payload["message"] = f"Accepted name already used by group {conflict_group_id}"
    payload["conflict_group_id"] = conflict_group_id
    payload["hint"] = "Choose a different candidate in this group"
  return payload


def _sync_group_resolution_state(
  payload: dict[str, Any],
  group: dict[str, Any],
  group_id: str,
  *,
  preferred_accepted_name: str | None = None,
) -> dict[str, Any]:
  store = ReviewSidecarStore()
  rejected_map = dict(payload.get("rejected_candidates", {}))
  rejected_ids = set(str(item).strip() for item in rejected_map.get(group_id, []))
  active_spellings = _active_spellings(group, rejected_ids)

  accepted_name = (preferred_accepted_name or "").strip()
  if not accepted_name:
    accepted_name = str(dict(payload.get("accepted_names", {})).get(group_id, "")).strip()
  if accepted_name and accepted_name not in active_spellings:
    accepted_name = ""
  if not accepted_name and len(active_spellings) == 1:
    accepted_name = active_spellings[0]

  if accepted_name:
    payload = store.set_group_consensus(payload, group_id, accepted_name)
  else:
    payload = store.set_group_accepted_name(payload, group_id, None)
    payload = store.set_group_resolution_status(payload, group_id, "UNRESOLVED")
    payload = store.set_group_collapsed(payload, group_id, False)
  return payload


class GroupMutationService:
  @staticmethod
  def apply_action(
    session_payload: dict[str, Any],
    action_type: str,
    target_ids: list[str],
    action_payload: dict[str, Any],
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    """Apply review-group specific actions; return handled=False for legacy fallbacks."""
    payload = ReviewSidecarStore.ensure_group_state_maps(session_payload)
    groups = list(payload.get("groups", []))
    if not groups:
      return payload, None, False

    primary_target = str(target_ids[0]).strip() if target_ids else ""
    group_id = str(action_payload.get("group_id", "")).strip()
    if not group_id and primary_target and action_type in {"confirm", "reject", "unreject"}:
      group_id = _find_group_for_candidate(groups, primary_target) or ""

    if action_type == "confirm":
      if not group_id or not primary_target:
        return payload, None, False
      return GroupMutationService.confirm_candidate(payload, group_id, primary_target)
    if action_type == "reject":
      if not group_id or not primary_target:
        return payload, None, False
      return GroupMutationService.reject_candidate(payload, group_id, primary_target)
    if action_type == "unreject":
      if not group_id or not primary_target:
        return payload, None, False
      return GroupMutationService.unreject_candidate(payload, group_id, primary_target)
    if action_type == "deselect":
      if not group_id:
        return payload, None, False
      return GroupMutationService.deselect_group(payload, group_id)
    if action_type == "toggle_collapse":
      if not group_id:
        return payload, None, False
      requested = action_payload.get("is_collapsed")
      if requested is None:
        current = bool(payload.get("collapsed_groups", {}).get(group_id, False))
        requested = not current
      return GroupMutationService.toggle_group_collapsed(payload, group_id, bool(requested))

    return payload, None, False

  @staticmethod
  def confirm_candidate(
    session_payload: dict[str, Any],
    group_id: str,
    candidate_id: str,
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    store = ReviewSidecarStore()
    payload = store.ensure_group_state_maps(session_payload)
    group = _find_group(list(payload.get("groups", [])), group_id)
    if group is None:
      return payload, None, False

    candidate = _find_candidate(group, candidate_id)
    if candidate is None:
      return payload, None, False

    accepted_name = _candidate_name(candidate)
    conflict_group = _duplicate_conflict(
      _accepted_name_lookup(payload),
      accepted_name,
      excluded_group_id=group_id,
    )
    if conflict_group:
      return payload, _validation_payload(
        is_valid=False,
        candidate_name=accepted_name,
        conflict_group_id=conflict_group,
      ), True

    updated = store.set_candidate_rejected(payload, group_id, candidate_id, False)
    updated = _sync_group_resolution_state(
      updated,
      group,
      group_id,
      preferred_accepted_name=accepted_name,
    )
    rejected_ids = set(dict(updated.get("rejected_candidates", {})).get(group_id, []))
    updated["candidates"] = _set_group_candidate_statuses(
      list(updated.get("candidates", [])),
      group,
      rejected_ids,
      candidate_id,
    )
    return updated, _validation_payload(is_valid=True, candidate_name=accepted_name), True

  @staticmethod
  def reject_candidate(
    session_payload: dict[str, Any],
    group_id: str,
    candidate_id: str,
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    store = ReviewSidecarStore()
    payload = store.ensure_group_state_maps(session_payload)
    group = _find_group(list(payload.get("groups", [])), group_id)
    if group is None:
      return payload, None, False

    candidate = _find_candidate(group, candidate_id)
    if candidate is None:
      return payload, None, False

    candidate_name = _candidate_name(candidate)
    updated = store.set_candidate_rejected(payload, group_id, candidate_id, True)
    preferred_accepted_name = str(dict(updated.get("accepted_names", {})).get(group_id, "")).strip()
    if preferred_accepted_name == candidate_name:
      preferred_accepted_name = ""
    updated = _sync_group_resolution_state(
      updated,
      group,
      group_id,
      preferred_accepted_name=preferred_accepted_name,
    )
    rejected_ids = set(dict(updated.get("rejected_candidates", {})).get(group_id, []))
    confirmed_candidate_id = None
    if preferred_accepted_name:
      for group_candidate in list(group.get("candidates", [])):
        if _candidate_name(group_candidate) == preferred_accepted_name:
          confirmed_candidate_id = str(group_candidate.get("candidate_id", "")).strip()
          break
    updated["candidates"] = _set_group_candidate_statuses(
      list(updated.get("candidates", [])),
      group,
      rejected_ids,
      confirmed_candidate_id,
    )
    return updated, None, True

  @staticmethod
  def unreject_candidate(
    session_payload: dict[str, Any],
    group_id: str,
    candidate_id: str,
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    store = ReviewSidecarStore()
    payload = store.ensure_group_state_maps(session_payload)
    group = _find_group(list(payload.get("groups", [])), group_id)
    if group is None:
      return payload, None, False
    candidate = _find_candidate(group, candidate_id)
    if candidate is None:
      return payload, None, False

    updated = store.set_candidate_rejected(payload, group_id, candidate_id, False)
    updated = _sync_group_resolution_state(updated, group, group_id)
    rejected_ids = set(dict(updated.get("rejected_candidates", {})).get(group_id, []))
    accepted_name = str(dict(updated.get("accepted_names", {})).get(group_id, "")).strip()
    confirmed_candidate_id = None
    if accepted_name:
      for group_candidate in list(group.get("candidates", [])):
        if _candidate_name(group_candidate) == accepted_name:
          confirmed_candidate_id = str(group_candidate.get("candidate_id", "")).strip()
          break
    updated["candidates"] = _set_group_candidate_statuses(
      list(updated.get("candidates", [])),
      group,
      rejected_ids,
      confirmed_candidate_id,
    )
    return updated, None, True

  @staticmethod
  def deselect_group(
    session_payload: dict[str, Any],
    group_id: str,
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    store = ReviewSidecarStore()
    payload = store.ensure_group_state_maps(session_payload)
    if _find_group(list(payload.get("groups", [])), group_id) is None:
      return payload, None, False

    group = _find_group(list(payload.get("groups", [])), group_id)
    if group is None:
      return payload, None, False

    updated = store.set_group_accepted_name(payload, group_id, None)
    updated = store.set_group_resolution_status(updated, group_id, "UNRESOLVED")
    updated = store.set_group_collapsed(updated, group_id, False)
    rejected_ids = set(dict(updated.get("rejected_candidates", {})).get(group_id, []))
    updated["candidates"] = _set_group_candidate_statuses(
      list(updated.get("candidates", [])),
      group,
      rejected_ids,
      None,
    )
    return updated, None, True

  @staticmethod
  def toggle_group_collapsed(
    session_payload: dict[str, Any],
    group_id: str,
    is_collapsed: bool,
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    store = ReviewSidecarStore()
    payload = store.ensure_group_state_maps(session_payload)
    if _find_group(list(payload.get("groups", [])), group_id) is None:
      return payload, None, False
    updated = store.set_group_collapsed(payload, group_id, is_collapsed)
    return updated, None, True

  @staticmethod
  def move_candidate(groups: list[dict], candidate_id: str, to_group_id: str) -> list[dict]:
    moving = None
    for group in groups:
      for candidate in list(group.get("candidates", [])):
        if candidate.get("candidate_id") == candidate_id:
          moving = candidate
          group["candidates"].remove(candidate)
          break
    if moving is None:
      return groups
    for group in groups:
      if group.get("group_id") == to_group_id:
        group.setdefault("candidates", []).append(moving)
        break
    return groups

  @staticmethod
  def merge_groups(groups: list[dict], group_a_id: str, group_b_id: str) -> list[dict]:
    a = next((g for g in groups if g.get("group_id") == group_a_id), None)
    b = next((g for g in groups if g.get("group_id") == group_b_id), None)
    if a is None or b is None:
      return groups
    a.setdefault("candidates", []).extend(b.get("candidates", []))
    return [g for g in groups if g.get("group_id") != group_b_id]

  @staticmethod
  def reorder_group(groups: list[dict], group_id: str, to_index: int) -> list[dict]:
    idx = next((i for i, g in enumerate(groups) if g.get("group_id") == group_id), None)
    if idx is None:
      return groups
    group = groups.pop(idx)
    bounded = max(0, min(to_index, len(groups)))
    groups.insert(bounded, group)
    return groups
