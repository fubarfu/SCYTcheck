from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.config import AdvancedSettings, AppConfig
from src.data.models import ContextPattern, PlayerSummary, VideoAnalysis
import src.main as app_main


class _FakeButton:
    def __init__(self) -> None:
        self.command = None

    def configure(self, **kwargs) -> None:
        self.command = kwargs.get("command")


class _FakeRoot:
    def __init__(self) -> None:
        self.window = None

    def mainloop(self) -> None:
        if self.window and self.window.analyze_button.command:
            self.window.analyze_button.command()


class _FakeWindow:
    def __init__(self, root: _FakeRoot, url: str, output_folder: str, settings: AdvancedSettings) -> None:
        self.root = root
        self.root.window = self
        self.url_input = SimpleNamespace(get=lambda: url)
        self.file_selector = SimpleNamespace(get=lambda: output_folder)
        self.progress = Mock()
        self.analyze_button = _FakeButton()
        self.retry_export_button = _FakeButton()
        self.apply_advanced_settings = Mock()
        self.get_advanced_settings = Mock(return_value=settings)
        self.set_status = Mock()


def _run_main_once(
    tmp_path: Path,
    analysis: VideoAnalysis,
    logging_enabled: bool = False,
    export_side_effect=None,
    trigger_retry: bool = False,
    selected_region_times: list[float] | None = None,
):
    root = _FakeRoot()
    window_holder: dict[str, _FakeWindow] = {}

    settings = AdvancedSettings(
        context_patterns=[{"id": "pattern-1", "before_text": "Player:", "after_text": None, "enabled": True}],
        filter_non_matching=True,
        event_gap_threshold_sec=1.5,
        ocr_confidence_threshold=12,
        video_quality="best",
        logging_enabled=logging_enabled,
    )

    logger = Mock()
    video_service = Mock()
    video_service.validate_youtube_url.return_value = (True, "")
    ocr_service = Mock()
    ocr_service.confidence_threshold = 40
    analysis_service = Mock()
    analysis_service.analyze.return_value = analysis
    export_service = Mock()
    export_service.generate_filename.return_value = "out.csv"
    if export_side_effect is None:
        export_service.export_to_csv.return_value = tmp_path / "out.csv"
    else:
        export_service.export_to_csv.side_effect = export_side_effect
    region_selector = Mock()
    region_selector.select_regions.return_value = [(10, 20, 100, 50)]
    region_selector.selected_regions = [
        (10, 20, 100, 50, value)
        for value in (selected_region_times if selected_region_times is not None else [0.0])
    ]

    def make_window(root_arg):
        window = _FakeWindow(root_arg, "https://youtube.com/watch?v=test", str(tmp_path), settings)
        window_holder["window"] = window
        return window

    with patch("src.main.load_config", return_value=AppConfig(sample_fps=1, confidence_threshold=40, tesseract_cmd=None)), patch(
        "src.main.configure_logging", return_value=logger
    ), patch("src.main.VideoService", return_value=video_service), patch(
        "src.main.OCRService", return_value=ocr_service
    ), patch("src.main.AnalysisService", return_value=analysis_service), patch(
        "src.main.ExportService", return_value=export_service
    ), patch("src.main.RegionSelector", return_value=region_selector), patch(
        "src.main.tk.Tk", return_value=root
    ), patch("src.main.MainWindow", side_effect=make_window), patch(
        "src.main.load_advanced_settings", return_value=settings
    ) as load_settings, patch("src.main.save_advanced_settings") as save_settings, patch(
        "src.main.messagebox.showinfo"
    ) as show_info, patch("src.main.messagebox.showerror") as show_error:
        app_main.main()
        retry_command = window_holder["window"].retry_export_button.command
        if trigger_retry and retry_command is not None:
            retry_command()

    return {
        "window": window_holder["window"],
        "load_settings": load_settings,
        "save_settings": save_settings,
        "video_service": video_service,
        "ocr_service": ocr_service,
        "analysis_service": analysis_service,
        "export_service": export_service,
        "region_selector": region_selector,
        "show_info": show_info,
        "show_error": show_error,
        "settings": settings,
    }


def test_main_loads_settings_and_wires_analysis_flow(tmp_path: Path) -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=test")
    analysis.set_player_summaries(
        [
            PlayerSummary(
                player_name="Alice",
                start_timestamp="00:00:01.000",
                normalized_name="alice",
                occurrence_count=1,
                first_seen_sec=1.0,
                last_seen_sec=1.0,
                representative_region="10:20:100:50",
            )
        ]
    )

    result = _run_main_once(tmp_path, analysis)

    result["load_settings"].assert_called_once()
    result["window"].apply_advanced_settings.assert_called_once_with(result["settings"])
    result["save_settings"].assert_called_once()
    assert result["ocr_service"].confidence_threshold == 12
    result["video_service"].validate_youtube_url.assert_called_once()
    result["region_selector"].select_regions.assert_called_once()
    result["analysis_service"].analyze.assert_called_once()
    analyze_kwargs = result["analysis_service"].analyze.call_args.kwargs
    assert analyze_kwargs["filter_non_matching"] is True
    assert analyze_kwargs["event_gap_threshold_sec"] == 1.5
    assert analyze_kwargs["context_patterns"] == [
        ContextPattern(id="pattern-1", before_text="Player:", after_text=None, enabled=True)
    ]
    assert result["window"].progress.set_stage.call_args_list[0].args == ("Detect",)
    assert result["window"].progress.set_stage.call_args_list[1].args == ("Aggregate",)
    assert result["window"].progress.set_stage.call_args_list[2].args == ("Export",)
    result["export_service"].generate_filename.assert_called_once()
    result["export_service"].export_to_csv.assert_called_once()
    result["show_error"].assert_not_called()


def test_main_shows_header_only_completion_message_when_no_text_detected(tmp_path: Path) -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=test")

    result = _run_main_once(tmp_path, analysis)

    result["show_info"].assert_called_once()
    title, message = result["show_info"].call_args.args
    assert title == "Analysis Complete"
    assert "No matching text was detected" in message
    assert "out.csv" in message


def test_main_does_not_write_sidecar_log_when_logging_disabled(tmp_path: Path) -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=test")
    analysis.set_player_summaries(
        [
            PlayerSummary(
                player_name="Alice",
                start_timestamp="00:00:01.000",
                normalized_name="alice",
                occurrence_count=1,
                first_seen_sec=1.0,
                last_seen_sec=1.0,
                representative_region="10:20:100:50",
            )
        ]
    )

    with patch("src.main.write_sidecar_log") as write_sidecar_log:
        result = _run_main_once(tmp_path, analysis, logging_enabled=False)

    write_sidecar_log.assert_not_called()
    result["show_error"].assert_not_called()


def test_main_retries_export_without_rerunning_analysis(tmp_path: Path) -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=test")
    analysis.set_player_summaries(
        [
            PlayerSummary(
                player_name="Alice",
                start_timestamp="00:00:01.000",
                normalized_name="alice",
                occurrence_count=1,
                first_seen_sec=1.0,
                last_seen_sec=1.0,
                representative_region="10:20:100:50",
            )
        ]
    )

    result = _run_main_once(
        tmp_path,
        analysis,
        export_side_effect=[OSError("file is locked"), tmp_path / "out.csv"],
        trigger_retry=True,
    )

    assert result["analysis_service"].analyze.call_count == 1
    assert result["export_service"].export_to_csv.call_count == 2
    result["show_error"].assert_called_once_with("Export Error", "file is locked")
    result["show_info"].assert_called_once_with("Export Complete", f"CSV exported to:\n{tmp_path / 'out.csv'}")


def test_main_uses_selected_region_time_as_analysis_start(tmp_path: Path) -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=test")
    analysis.set_player_summaries(
        [
            PlayerSummary(
                player_name="Alice",
                start_timestamp="00:03:05.000",
                normalized_name="alice",
                occurrence_count=1,
                first_seen_sec=185.0,
                last_seen_sec=185.0,
                representative_region="10:20:100:50",
            )
        ]
    )

    result = _run_main_once(tmp_path, analysis, selected_region_times=[185.0])
    kwargs = result["analysis_service"].analyze.call_args.kwargs

    assert kwargs["start_time"] == 185.0
    assert kwargs["end_time"] == 245.0
