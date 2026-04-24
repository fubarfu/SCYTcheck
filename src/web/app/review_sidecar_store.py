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
