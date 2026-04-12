from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class URLInput:
    def __init__(self, parent: tk.Widget, label_text: str = "YouTube URL") -> None:
        self.label = ttk.Label(parent, text=label_text)
        self.entry = ttk.Entry(parent, width=70)

    def grid(self, row: int, column: int, columnspan: int = 1) -> None:
        self.label.grid(row=row, column=column, sticky="w", pady=(4, 2))
        self.entry.grid(row=row + 1, column=column, columnspan=columnspan, sticky="ew")

    def get(self) -> str:
        return self.entry.get().strip()
