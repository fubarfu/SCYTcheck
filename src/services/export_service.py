from __future__ import annotations

import csv
from pathlib import Path

from src.data.models import VideoAnalysis


class ExportService:
    HEADERS = ["Text", "X", "Y", "Width", "Height", "Frequency"]

    def export_to_csv(self, analysis: VideoAnalysis, output_path: str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(self.HEADERS)
            for entry in analysis.text_strings:
                writer.writerow(
                    [
                        entry.content,
                        entry.x,
                        entry.y,
                        entry.width,
                        entry.height,
                        entry.frequency,
                    ]
                )

        return path
