from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class FileSelector:
    def __init__(self, parent: tk.Widget, label_text: str = "Output Folder") -> None:
        self.label = ttk.Label(parent, text=label_text)
        self.path_var = tk.StringVar(value="")
        self.entry = ttk.Entry(parent, textvariable=self.path_var, width=55)
        self.button = ttk.Button(parent, text="Browse...", command=self._choose)

    def grid(self, row: int, column: int, columnspan: int = 1) -> None:
        self.label.grid(row=row, column=column, sticky="w", pady=(8, 2))
        self.entry.grid(row=row + 1, column=column, columnspan=max(1, columnspan - 1), sticky="ew")
        self.button.grid(row=row + 1, column=column + columnspan - 1, sticky="e", padx=(8, 0))

    def _choose(self) -> None:
        """Open folder selection dialog (folder-only mode)."""
        selected = filedialog.askdirectory(
            title="Select output folder for CSV analysis results"
        )
        if selected:
            self.path_var.set(selected)

    def get(self) -> str:
        """Get selected folder path."""
        return self.path_var.get().strip()
    
    def show_error(self, title: str, message: str) -> None:
        """Display error dialog to user."""
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str) -> None:
        """Display info dialog to user."""
        messagebox.showinfo(title, message)
