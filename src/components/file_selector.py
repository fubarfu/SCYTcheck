from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class FileSelector:
    """UI component for selecting output folder with validation and error feedback."""
    
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
    
    def validate_selected_folder(self) -> tuple[bool, str]:
        """
        Validate the currently selected folder.
        
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if folder is valid
            - error_message: User-friendly error description if invalid
        """
        folder_path = self.get()
        
        # Check if folder was selected
        if not folder_path:
            return False, "Please select an output folder before proceeding."
        
        folder = Path(folder_path)
        
        # Check if folder exists
        if not folder.exists():
            return False, (
                f"Output folder does not exist:\n\n{folder_path}\n\n"
                "Please select a valid folder, or create it before proceeding."
            )
        
        # Check if path is a directory
        if not folder.is_dir():
            return False, (
                f"Selected path is not a directory:\n\n{folder_path}\n\n"
                "Please select a folder, not a file."
            )
        
        # Check if folder is writable
        if not os.access(folder, os.W_OK):
            return False, (
                f"Output folder is not writable:\n\n{folder_path}\n\n"
                "Please check folder permissions and try again."
            )
        
        return True, ""
    
    def show_error(self, title: str, message: str) -> None:
        """Display error dialog to user."""
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str) -> None:
        """Display info dialog to user."""
        messagebox.showinfo(title, message)
    
    def show_validation_error(self) -> bool:
        """
        Validate selected folder and show error dialog if invalid.
        
        Returns:
            True if folder is valid, False otherwise
        """
        is_valid, error_msg = self.validate_selected_folder()
        
        if not is_valid:
            self.show_error("Invalid Output Folder", error_msg)
        
        return is_valid
    
    def set_path(self, path: str) -> None:
        """Set the folder path programmatically."""
        self.path_var.set(path)
