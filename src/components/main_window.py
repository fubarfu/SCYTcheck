from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.components.file_selector import FileSelector
from src.components.progress_display import ProgressDisplay
from src.components.url_input import URLInput


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SCYTcheck - YouTube Text Analyzer")
        self.root.minsize(720, 260)

        container = ttk.Frame(root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=0)

        self.url_input = URLInput(container)
        self.url_input.grid(row=0, column=0, columnspan=2)

        self.file_selector = FileSelector(container)
        self.file_selector.grid(row=2, column=0, columnspan=2)

        self.progress = ProgressDisplay(container)
        self.progress.grid(row=4, column=0, columnspan=2)

        self.status = ttk.Label(container, text="Ready")
        self.status.grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.analyze_button = ttk.Button(container, text="Select Regions + Analyze")
        self.analyze_button.grid(row=7, column=0, sticky="w", pady=(12, 0))

    def set_status(self, value: str) -> None:
        self.status.configure(text=value)
        self.status.update_idletasks()
