from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    schema_version: str
    missing_columns: tuple[str, ...] = ()
    error: str | None = None


class ResultSchemaValidator:
    """Validates result CSV headers before loading into a review session."""

    DEFAULT_REQUIRED_COLUMNS = ("PlayerName", "StartTimestamp")
    SUPPORTED_SCHEMA_VERSIONS = {"1.0"}

    def __init__(self, required_columns: tuple[str, ...] | None = None) -> None:
        self.required_columns = required_columns or self.DEFAULT_REQUIRED_COLUMNS

    def validate(self, csv_path: Path | str) -> ValidationResult:
        path = Path(csv_path)
        if not path.exists():
            return ValidationResult(
                is_valid=False,
                schema_version="unknown",
                error=f"CSV file not found: {path}",
            )

        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            rows = [row for row in reader if row]

        if not rows:
            return ValidationResult(
                is_valid=False,
                schema_version="unknown",
                error="CSV is empty",
            )

        schema_version = "1.0"
        header_row = rows[0]
        if header_row and header_row[0].startswith("#schema_version="):
            schema_version = header_row[0].split("=", maxsplit=1)[1].strip() or "unknown"
            if len(rows) < 2:
                return ValidationResult(
                    is_valid=False,
                    schema_version=schema_version,
                    error="CSV has schema metadata but no header row",
                )
            header_row = rows[1]

        if schema_version not in self.SUPPORTED_SCHEMA_VERSIONS:
            return ValidationResult(
                is_valid=False,
                schema_version=schema_version,
                error=f"Unsupported schema_version: {schema_version}",
            )

        missing = tuple(col for col in self.required_columns if col not in header_row)
        if missing:
            return ValidationResult(
                is_valid=False,
                schema_version=schema_version,
                missing_columns=missing,
                error="Missing required CSV columns",
            )

        return ValidationResult(is_valid=True, schema_version=schema_version)
