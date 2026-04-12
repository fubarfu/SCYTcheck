from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.components.progress_display import ProgressDisplay


def test_set_progress_flushes_bar_and_toplevel() -> None:
    parent = MagicMock()
    with (
        patch("src.components.progress_display.tk.IntVar") as mock_var,
        patch("src.components.progress_display.ttk.Label") as mock_label,
        patch("src.components.progress_display.ttk.Progressbar") as mock_bar,
    ):
        variable = MagicMock()
        label = MagicMock()
        bar = MagicMock()
        toplevel = MagicMock()
        mock_var.return_value = variable
        mock_label.return_value = label
        mock_bar.return_value = bar
        bar.winfo_toplevel.return_value = toplevel

        display = ProgressDisplay(parent)
        display.set_progress(42)

    variable.set.assert_called_once_with(42)
    label.configure.assert_called_with(text="Detect: 42%")
    label.update_idletasks.assert_called()
    bar.update_idletasks.assert_called()
    toplevel.update_idletasks.assert_called()


def test_set_stage_flushes_bar_and_toplevel() -> None:
    parent = MagicMock()
    with (
        patch("src.components.progress_display.tk.IntVar") as mock_var,
        patch("src.components.progress_display.ttk.Label") as mock_label,
        patch("src.components.progress_display.ttk.Progressbar") as mock_bar,
    ):
        variable = MagicMock()
        variable.get.return_value = 7
        label = MagicMock()
        bar = MagicMock()
        toplevel = MagicMock()
        mock_var.return_value = variable
        mock_label.return_value = label
        mock_bar.return_value = bar
        bar.winfo_toplevel.return_value = toplevel

        display = ProgressDisplay(parent)
        display.set_stage("Export")

    label.configure.assert_called_with(text="Export: 7%")
    label.update_idletasks.assert_called()
    bar.update_idletasks.assert_called()
    toplevel.update_idletasks.assert_called()
