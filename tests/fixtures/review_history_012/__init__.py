from __future__ import annotations

from pathlib import Path
from typing import Any


def build_workspace_csv(tmp_path: Path, name: str = "review_history_012") -> Path:
    csv_path = tmp_path / f"{name}.csv"
    csv_path.write_text(
        "#schema_version=1.0\n"
        "PlayerName,StartTimestamp\n"
        "Alice,00:00:01.000\n"
        "Alicia,00:00:01.200\n",
        encoding="utf-8",
    )
    return csv_path


def build_history_entry(entry_id: str, group_count: int = 2) -> dict[str, Any]:
    resolved = 1 if group_count > 0 else 0
    unresolved = max(0, group_count - resolved)
    return {
        "entry_id": entry_id,
        "created_at": "2026-04-27T12:00:00+00:00",
        "trigger_type": "confirm",
        "compressed": False,
        "summary": {
            "group_count": group_count,
            "resolved_count": resolved,
            "unresolved_count": unresolved,
        },
        "snapshot": {
            "group_count": group_count,
            "resolved_count": resolved,
            "unresolved_count": unresolved,
            "groups": [],
            "reviewed_names": ["Alice"],
        },
    }
