from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ProgressDisplay:
    def __init__(self, parent: tk.Widget) -> None:
        self.variable = tk.IntVar(value=0)
        self.stage = "Detect"
        self.label = ttk.Label(parent, text="Detect: 0%")
        self.bar = ttk.Progressbar(parent, orient="horizontal", mode="determinate", maximum=100)
        self.bar.configure(variable=self.variable)

    def _flush_ui(self) -> None:
        self.label.update_idletasks()
        self.bar.update_idletasks()
        try:
            self.bar.winfo_toplevel().update_idletasks()
        except Exception:
            return

    def grid(self, row: int, column: int, columnspan: int = 1) -> None:
        self.label.grid(row=row, column=column, columnspan=columnspan, sticky="w", pady=(8, 2))
        self.bar.grid(row=row + 1, column=column, columnspan=columnspan, sticky="ew")

    def set_progress(self, value: int) -> None:
        bounded = max(0, min(value, 100))
        self.variable.set(bounded)
        self.label.configure(text=f"{self.stage}: {bounded}%")
        self._flush_ui()

    def set_stage(self, stage: str) -> None:
        self.stage = stage
        self.label.configure(text=f"{self.stage}: {self.variable.get()}%")
        self._flush_ui()
