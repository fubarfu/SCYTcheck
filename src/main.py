from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from src.components.main_window import MainWindow
from src.components.region_selector import RegionSelector
from src.config import load_advanced_settings, load_config
from src.data.models import ContextPattern
from src.services.analysis_service import AnalysisService
from src.services.export_service import ExportService
from src.services.logging import configure_logging
from src.services.ocr_service import OCRService
from src.services.video_service import InvalidURLError, VideoAccessError, VideoService


def main() -> None:
    config = load_config()
    logger = configure_logging()

    video_service = VideoService()
    ocr_service = OCRService(
        confidence_threshold=config.confidence_threshold,
        tesseract_cmd=config.tesseract_cmd,
    )
    analysis_service = AnalysisService(video_service=video_service, ocr_service=ocr_service)
    export_service = ExportService()
    region_selector = RegionSelector(video_service)

    root = tk.Tk()
    window = MainWindow(root)

    def run_analysis() -> None:
        url = window.url_input.get()
        output_folder = window.file_selector.get()

        if not url:
            messagebox.showerror("Missing URL", "Please enter a YouTube URL.")
            return

        if not output_folder:
            messagebox.showerror("Missing Output Folder", "Please choose an output folder.")
            return

        try:
            is_valid, validation_error = video_service.validate_youtube_url(url)
            if not is_valid:
                window.set_status("Invalid URL")
                messagebox.showerror("Invalid URL", validation_error)
                return

            advanced = load_advanced_settings()
            context_patterns = [
                ContextPattern(
                    id=str(item.get("id", f"pattern-{index}")),
                    before_text=str(item["before_text"]) if item.get("before_text") is not None else None,
                    after_text=str(item["after_text"]) if item.get("after_text") is not None else None,
                    enabled=bool(item.get("enabled", True)),
                )
                for index, item in enumerate(advanced.context_patterns)
            ]

            window.set_status("Selecting regions...")
            regions = region_selector.select_regions(url, frame_time_seconds=0.0)
            if not regions:
                window.set_status("No regions selected")
                return

            window.progress.set_stage("Detect")
            window.set_status("Analyzing video...")
            analysis = analysis_service.analyze(
                url=url,
                regions=regions,
                start_time=0,
                end_time=60,
                fps=config.sample_fps,
                on_progress=window.progress.set_progress,
                context_patterns=context_patterns,
                filter_non_matching=advanced.filter_non_matching,
                event_gap_threshold_sec=advanced.event_gap_threshold_sec,
            )

            window.progress.set_stage("Aggregate")
            window.progress.set_progress(100)

            filename = export_service.generate_filename(url)
            window.progress.set_stage("Export")
            exported = export_service.export_to_csv(analysis, output_folder, filename)
            window.set_status(f"Completed: {exported}")
            if not analysis.player_summaries:
                messagebox.showinfo(
                    "Analysis Complete",
                    "No matching text was detected. A header-only CSV was exported to:\n"
                    f"{exported}",
                )
            else:
                messagebox.showinfo("Analysis Complete", f"CSV exported to:\n{exported}")

        except InvalidURLError as exc:
            logger.exception("Invalid YouTube URL")
            messagebox.showerror("Invalid URL", str(exc))
            window.set_status("Invalid URL")
        except VideoAccessError as exc:
            logger.exception("Video access error")
            messagebox.showerror("Video Error", str(exc))
            window.set_status("Video access error")
        except Exception as exc:  # pragma: no cover - UI safety net
            logger.exception("Unexpected application error")
            messagebox.showerror("Unexpected Error", str(exc))
            window.set_status("Unexpected error")

    window.analyze_button.configure(command=run_analysis)
    root.mainloop()


if __name__ == "__main__":
    main()
