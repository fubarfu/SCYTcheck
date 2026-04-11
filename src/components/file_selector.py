from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk


class FileSelector:
    def __init__(self, parent: tk.Widget, label_text: str = "Output CSV") -> None:
        self.label = ttk.Label(parent, text=label_text)
        self.path_var = tk.StringVar(value="")
        self.entry = ttk.Entry(parent, textvariable=self.path_var, width=55)
        self.button = ttk.Button(parent, text="Browse...", command=self._choose)

    def grid(self, row: int, column: int, columnspan: int = 1) -> None:
        self.label.grid(row=row, column=column, sticky="w", pady=(8, 2))
        self.entry.grid(row=row + 1, column=column, columnspan=max(1, columnspan - 1), sticky="ew")
        self.button.grid(row=row + 1, column=column + columnspan - 1, sticky="e", padx=(8, 0))

    def _choose(self) -> None:
        selected = filedialog.asksaveasfilename(
            title="Save analysis as CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if selected:
            self.path_var.set(selected)

    def get(self) -> str:
        return self.path_var.get().strip()
