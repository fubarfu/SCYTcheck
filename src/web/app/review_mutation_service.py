from __future__ import annotations

STATE_CHANGING_ACTIONS = frozenset(
    {
        "confirm",
        "reject",
        "unreject",
        "deselect",
        "edit",
        "remove",
        "move_candidate",
        "merge_groups",
        "reorder_group",
    }
)


def should_create_snapshot_for_action(action_type: str) -> bool:
    """Snapshot only for actions that mutate durable review state."""
    return action_type in STATE_CHANGING_ACTIONS
