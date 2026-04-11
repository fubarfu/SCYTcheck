from __future__ import annotations

import csv
import os
from pathlib import Path

from src.data.models import VideoAnalysis


class ExportService:
    HEADERS = ["Text", "X", "Y", "Width", "Height", "Frequency"]

    def validate_output_folder(self, folder_path: str) -> tuple[bool, str]:
        """
        Validate that the output folder exists and is writable.
        
        Args:
            folder_path: Path to the output folder
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if folder is valid and writable
            - error_message: Empty string if valid, otherwise descriptive error message
        """
        folder = Path(folder_path)
        
        # Check if folder exists
        if not folder.exists():
            return False, f"Output folder does not exist: {folder_path}"
        
        # Check if path is actually a directory
        if not folder.is_dir():
            return False, f"Path is not a directory: {folder_path}"
        
        # Check if folder is writable
        if not os.access(folder, os.W_OK):
            return False, f"Output folder is not writable: {folder_path}"
        
        return True, ""

    def export_to_csv(self, analysis: VideoAnalysis, output_folder: str, filename: str) -> Path:
        """
        Export analysis results to CSV file in the specified output folder.
        
        Args:
            analysis: VideoAnalysis object containing detected text strings
            output_folder: Directory path where CSV will be saved
            filename: Name of the CSV file to create
            
        Returns:
            Path to the created CSV file
        """
        folder = Path(output_folder)
        folder.mkdir(parents=True, exist_ok=True)
        
        output_path = folder / filename
        
        with output_path.open("w", newline="", encoding="utf-8") as file:
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

        return output_path
