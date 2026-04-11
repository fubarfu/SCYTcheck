from __future__ import annotations

import csv
import os
import re
from datetime import datetime
from pathlib import Path

from src.data.models import PlayerSummary, VideoAnalysis


class ExportService:
    LEGACY_HEADERS = ["Text", "X", "Y", "Width", "Height", "Frequency"]
    SUMMARY_HEADERS = [
        "PlayerName",
        "NormalizedName",
        "OccurrenceCount",
        "FirstSeenSec",
        "LastSeenSec",
        "RepresentativeRegion",
    ]

    @staticmethod
    def player_summary_to_row(summary: PlayerSummary) -> list[str | int | float]:
        return [
            summary.player_name,
            summary.normalized_name,
            summary.occurrence_count,
            f"{summary.first_seen_sec:.3f}",
            f"{summary.last_seen_sec:.3f}",
            summary.representative_region,
        ]

    @staticmethod
    def extract_youtube_video_id(url: str) -> str:
        """
        Extract video ID from YouTube URL.
        Supports standard youtube.com and youtu.be short URLs.
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID string
            
        Raises:
            ValueError: If URL doesn't contain a valid video ID
        """
        # Pattern for youtube.com URLs
        match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)', url)
        if match:
            return match.group(1)
        
        raise ValueError(f"Could not extract video ID from URL: {url}")

    @staticmethod
    def generate_filename(video_url: str, timestamp: datetime | None = None) -> str:
        """
        Generate auto-filename for CSV export.
        Format: scytcheck_<videoId>_<YYYYMMDD-HHMMSS>.csv
        
        Args:
            video_url: YouTube video URL
            timestamp: DateTime for filename (defaults to current time)
            
        Returns:
            Generated filename string
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        video_id = ExportService.extract_youtube_video_id(video_url)
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        
        return f"scytcheck_{video_id}_{timestamp_str}.csv"

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
            should_write_summary_schema = bool(
                analysis.player_summaries
                or analysis.detections
                or analysis.context_patterns
            )

            if should_write_summary_schema:
                writer.writerow(self.SUMMARY_HEADERS)
                for summary in analysis.player_summaries:
                    writer.writerow(self.player_summary_to_row(summary))
            else:
                # Backward-compatible export for legacy text-string analyses.
                writer.writerow(self.LEGACY_HEADERS)
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
