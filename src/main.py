from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox

from src.components.main_window import MainWindow
from src.components.region_selector import RegionSelector
from src.config import load_advanced_settings, load_config, save_advanced_settings
from src.data.models import ContextPattern, VideoAnalysis
from src.services.analysis_service import AnalysisService
from src.services.export_service import ExportService
from src.services.logging import configure_logging, write_sidecar_log
from src.services.ocr_service import OCRService
from src.services.video_service import InvalidURLError, VideoAccessError, VideoService


def main() -> None:
    config = load_config()
    if config.tessdata_prefix and not os.getenv("TESSDATA_PREFIX"):
        os.environ["TESSDATA_PREFIX"] = config.tessdata_prefix
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
    window.apply_advanced_settings(load_advanced_settings())
    last_analysis: VideoAnalysis | None = None
    last_output_folder: str | None = None
    last_filename: str | None = None
    last_logging_enabled = False

    def set_retry_export_command(command) -> None:
        if hasattr(window, "set_retry_export_command"):
            window.set_retry_export_command(command)
        elif hasattr(window, "retry_export_button"):
            state = "disabled" if command is None else "normal"
            window.retry_export_button.configure(command=command, state=state)

    def set_analyze_command(command) -> None:
        if hasattr(window, "set_analyze_command"):
            window.set_analyze_command(command)
        else:
            window.analyze_button.configure(command=command)

    def retry_export() -> None:
        nonlocal last_analysis, last_output_folder, last_filename, last_logging_enabled
        if last_analysis is None or not last_output_folder or not last_filename:
            return
        try:
            exported = export_service.export_to_csv(
                last_analysis, last_output_folder, last_filename
            )
            if last_logging_enabled:
                write_sidecar_log(last_output_folder, last_filename, last_analysis.log_records)
            window.set_status(f"Completed: {exported}")
            set_retry_export_command(None)
            messagebox.showinfo("Export Complete", f"CSV exported to:\n{exported}")
        except Exception as exc:
            logger.exception("Export retry failed")
            messagebox.showerror("Export Error", str(exc))
            window.set_status("Export retry failed")

    def run_analysis() -> None:
        nonlocal last_analysis, last_output_folder, last_filename, last_logging_enabled
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

            advanced = window.get_advanced_settings()
            save_advanced_settings(advanced)
            ocr_service.confidence_threshold = int(
                max(0, min(advanced.ocr_confidence_threshold, 100))
            )
            context_patterns = [
                ContextPattern(
                    id=str(item.get("id", f"pattern-{index}")),
                    before_text=str(item["before_text"])
                    if item.get("before_text") is not None
                    else None,
                    after_text=str(item["after_text"])
                    if item.get("after_text") is not None
                    else None,
                    enabled=bool(item.get("enabled", True)),
                )
                for index, item in enumerate(advanced.context_patterns)
            ]

            window.set_status("Selecting regions...")
            regions = region_selector.select_regions(
                url, frame_time_seconds=0.0, quality=advanced.video_quality
            )
            if not regions:
                window.set_status("No regions selected")
                return

            analysis_start_time = 0.0
            selected_regions_with_time = getattr(region_selector, "selected_regions", None)
            if isinstance(selected_regions_with_time, list) and selected_regions_with_time:
                selected_times: list[float] = []
                for selected_region in selected_regions_with_time:
                    if not isinstance(selected_region, tuple) or len(selected_region) < 5:
                        continue
                    try:
                        selected_times.append(float(selected_region[4]))
                    except Exception:
                        continue
                if selected_times:
                    analysis_start_time = max(0.0, min(selected_times))
            analysis_end_time = analysis_start_time + 60.0

            window.progress.set_stage("Detect")
            window.set_status("Analyzing video...")
            analysis = analysis_service.analyze(
                url=url,
                regions=regions,
                start_time=analysis_start_time,
                end_time=analysis_end_time,
                fps=config.sample_fps,
                on_progress=window.progress.set_progress,
                context_patterns=context_patterns,
                filter_non_matching=advanced.filter_non_matching,
                event_gap_threshold_sec=advanced.event_gap_threshold_sec,
                video_quality=advanced.video_quality,
                logging_enabled=advanced.logging_enabled,
            )
            last_analysis = analysis
            last_output_folder = output_folder
            last_logging_enabled = advanced.logging_enabled

            window.progress.set_stage("Aggregate")
            window.progress.set_progress(100)

            filename = export_service.generate_filename(url)
            last_filename = filename
            window.progress.set_stage("Export")
            exported = export_service.export_to_csv(analysis, output_folder, filename)
            if advanced.logging_enabled:
                write_sidecar_log(output_folder, filename, analysis.log_records)
            window.set_status(f"Completed: {exported}")
            set_retry_export_command(None)
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
        except OSError as exc:
            logger.exception("Export error")
            messagebox.showerror("Export Error", str(exc))
            window.set_status("Export failed")
            if last_analysis is not None and last_output_folder and last_filename:
                set_retry_export_command(retry_export)
        except Exception as exc:  # pragma: no cover - UI safety net
            logger.exception("Unexpected application error")
            messagebox.showerror("Unexpected Error", str(exc))
            window.set_status("Unexpected error")

    set_analyze_command(run_analysis)
    set_retry_export_command(None)
    root.mainloop()


if __name__ == "__main__":
    main()
