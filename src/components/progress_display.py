from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ProgressDisplay:
    def __init__(self, parent: tk.Widget) -> None:
        self.variable = tk.IntVar(value=0)
        self.label = ttk.Label(parent, text="Progress: 0%")
        self.bar = ttk.Progressbar(parent, orient="horizontal", mode="determinate", maximum=100)
        self.bar.configure(variable=self.variable)

    def grid(self, row: int, column: int, columnspan: int = 1) -> None:
        self.label.grid(row=row, column=column, columnspan=columnspan, sticky="w", pady=(8, 2))
        self.bar.grid(row=row + 1, column=column, columnspan=columnspan, sticky="ew")

    def set_progress(self, value: int) -> None:
        bounded = max(0, min(value, 100))
        self.variable.set(bounded)
        self.label.configure(text=f"Progress: {bounded}%")
        self.label.update_idletasks()
