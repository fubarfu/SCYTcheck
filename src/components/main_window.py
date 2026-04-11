from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from src.components.file_selector import FileSelector
from src.components.progress_display import ProgressDisplay
from src.components.url_input import URLInput
from src.services.export_service import ExportService


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SCYTcheck - YouTube Text Analyzer")
        self.root.minsize(720, 320)

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

        # Add filename display section
        self.filename_label = ttk.Label(
            container, 
            text="Output Filename", 
            font=("TkDefaultFont", 9, "bold")
        )
        self.filename_label.grid(row=3, column=0, sticky="w", pady=(12, 2))
        
        self.filename_display = ttk.Label(
            container,
            text="(Filename will be generated from YouTube video ID)",
            foreground="gray",
            font=("TkDefaultFont", 9)
        )
        self.filename_display.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 0))

        self.progress = ProgressDisplay(container)
        self.progress.grid(row=5, column=0, columnspan=2)

        self.status = ttk.Label(container, text="Ready")
        self.status.grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.analyze_button = ttk.Button(container, text="Select Regions + Analyze")
        self.analyze_button.grid(row=7, column=0, sticky="w", pady=(12, 0))
    
    def update_filename_display(self, url: str | None = None) -> None:
        """
        Update the displayed filename based on the current URL.
        
        Args:
            url: YouTube URL (defaults to current URL input if None)
        """
        if url is None:
            url = self.url_input.get()
        
        if not url:
            self.filename_display.configure(
                text="(Enter a YouTube URL to generate filename)",
                foreground="gray"
            )
            return
        
        try:
            # Generate filename from URL and current timestamp
            filename = ExportService.generate_filename(url)
            self.filename_display.configure(
                text=filename,
                foreground="black"
            )
        except ValueError:
            self.filename_display.configure(
                text="(Invalid YouTube URL - filename will be generated from valid URL)",
                foreground="orange"
            )

    def set_status(self, value: str) -> None:
        self.status.configure(text=value)
        self.status.update_idletasks()
