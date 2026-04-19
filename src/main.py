from __future__ import annotations

import contextlib
import queue
import threading
import tkinter as tk
from tkinter import messagebox

from src.components.main_window import MainWindow
from src.components.region_selector import RegionSelector
from src.config import load_advanced_settings, load_config, save_advanced_settings
from src.data.models import ContextPattern, VideoAnalysis
from src.services.analysis_service import AnalysisService
from src.services.export_service import ExportService
from src.services.logging import SidecarLogWriter, configure_logging, write_sidecar_log
from src.services.ocr_service import OCRService
from src.services.video_service import InvalidURLError, VideoAccessError, VideoService


def main() -> None:
    config = load_config()
    logger = configure_logging()

    video_service = VideoService()
    ocr_service = OCRService(
        confidence_threshold=config.confidence_threshold,
        paddleocr_model_root=config.paddleocr_model_root,
    )
    analysis_service = AnalysisService(video_service=video_service, ocr_service=ocr_service)
    export_service = ExportService()
    region_selector = RegionSelector(video_service)

    root = tk.Tk()
    window = MainWindow(root)
    advanced_settings = load_advanced_settings()
    window.apply_advanced_settings(advanced_settings)
    last_analysis: VideoAnalysis | None = None
    last_output_folder: str | None = None
    last_filename: str | None = None
    last_logging_enabled = False
    ui_queue: queue.Queue[tuple[object, tuple[object, ...], dict[str, object]]] = queue.Queue()

    def dispatch_to_ui(callback, *args, **kwargs) -> None:
        if hasattr(root, "tk") and hasattr(root, "after"):
            ui_queue.put((callback, args, kwargs))
        else:
            callback(*args, **kwargs)

    def drain_ui_queue() -> None:
        while True:
            try:
                callback, args, kwargs = ui_queue.get_nowait()
            except queue.Empty:
                break
            callback(*args, **kwargs)

        if hasattr(root, "tk") and hasattr(root, "after"):
            root.after(25, drain_ui_queue)

    if hasattr(root, "tk") and hasattr(root, "after"):
        root.after(25, drain_ui_queue)

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
            ocr_service.paddleocr_model_root = (
                advanced.paddleocr_model_root or config.paddleocr_model_root
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

            window.progress.set_stage("Detect")
            window.progress.set_progress(1)
            window.set_status("Analyzing video...")

            def run_analysis_worker() -> None:
                nonlocal last_analysis, last_output_folder, last_filename, last_logging_enabled
                try:
                    # Analyze across the full video timeline. Region selection time is only
                    # for choosing representative ROIs, not for clipping analysis duration.
                    analysis_start_time = 0.0
                    video_info = video_service.get_video_info(
                        url,
                        quality=advanced.video_quality,
                    )
                    duration_value = video_info.get("duration", 0.0)
                    try:
                        analysis_end_time = float(duration_value)
                    except (TypeError, ValueError):
                        analysis_end_time = 0.0
                    if analysis_end_time <= analysis_start_time:
                        analysis_end_time = analysis_start_time + 60.0

                    # Generate filename early so it can be used for the sidecar log writer
                    filename = export_service.generate_filename(url)
                    last_filename = filename

                    # Determine whether to use SidecarLogWriter context
                    log_writer_ctx = (
                        SidecarLogWriter(output_folder, filename)
                        if advanced.logging_enabled
                        else contextlib.nullcontext()
                    )

                    with log_writer_ctx as writer:
                        analysis = analysis_service.analyze(
                            url=url,
                            regions=regions,
                            start_time=analysis_start_time,
                            end_time=analysis_end_time,
                            fps=config.sample_fps,
                            on_progress=lambda value: dispatch_to_ui(
                                window.progress.set_progress, value
                            ),
                            context_patterns=context_patterns,
                            filter_non_matching=advanced.filter_non_matching,
                            event_gap_threshold_sec=advanced.event_gap_threshold_sec,
                            video_quality=advanced.video_quality,
                            logging_enabled=advanced.logging_enabled,
                            tolerance_value=advanced.tolerance_value,
                            gating_enabled=advanced.gating_enabled,
                            gating_threshold=advanced.gating_threshold,
                            on_log_record=writer.write_record if advanced.logging_enabled else None,
                        )
                        last_analysis = analysis
                        last_output_folder = output_folder
                        last_logging_enabled = advanced.logging_enabled

                        dispatch_to_ui(window.progress.set_stage, "Aggregate")
                        dispatch_to_ui(window.progress.set_progress, 100)

                        dispatch_to_ui(window.progress.set_stage, "Export")
                        exported = export_service.export_to_csv(analysis, output_folder, filename)

                    gating_summary = ExportService.format_gating_summary(analysis.gating_stats)
                    timing_summary = ExportService.format_timing_summary(analysis.runtime_metrics)

                    dispatch_to_ui(
                        window.set_status,
                        f"Completed: {exported}{gating_summary}{timing_summary}",
                    )
                    dispatch_to_ui(set_retry_export_command, None)
                    if not analysis.player_summaries:
                        dispatch_to_ui(
                            messagebox.showinfo,
                            "Analysis Complete",
                            (
                                "No matching text was detected. "
                                "A header-only CSV was exported to:\n"
                                f"{exported}{gating_summary}{timing_summary}"
                            ),
                        )
                    else:
                        dispatch_to_ui(
                            messagebox.showinfo,
                            "Analysis Complete",
                            f"CSV exported to:\n{exported}{gating_summary}{timing_summary}",
                        )

                except InvalidURLError as exc:
                    logger.exception("Invalid YouTube URL")
                    dispatch_to_ui(messagebox.showerror, "Invalid URL", str(exc))
                    dispatch_to_ui(window.set_status, "Invalid URL")
                except VideoAccessError as exc:
                    logger.exception("Video access error")
                    dispatch_to_ui(messagebox.showerror, "Video Error", str(exc))
                    dispatch_to_ui(window.set_status, "Video access error")
                except OSError as exc:
                    logger.exception("Export error")
                    dispatch_to_ui(messagebox.showerror, "Export Error", str(exc))
                    dispatch_to_ui(window.set_status, "Export failed")
                    if last_analysis is not None and last_output_folder and last_filename:
                        dispatch_to_ui(set_retry_export_command, retry_export)
                except Exception as exc:  # pragma: no cover - UI safety net
                    logger.exception("Unexpected application error")
                    dispatch_to_ui(messagebox.showerror, "Unexpected Error", str(exc))
                    dispatch_to_ui(window.set_status, "Unexpected error")

            threading.Thread(target=run_analysis_worker, daemon=True).start()

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
