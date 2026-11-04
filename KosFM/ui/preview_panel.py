
"""
Preview panel widget for KosFM.
Shows a quick preview of the currently selected file or directory.
"""

import os
import tkinter as tk
from tkinter import ttk

from ..utils.file_utils import format_size, format_time, get_file_type


class PreviewPanel:
    """Preview panel that displays info and a snippet of selected items."""

    TEXT_PREVIEW_BYTES = 8 * 1024
    TEXT_MAX_LINES = 40

    def __init__(self, parent):
        """Initialize preview panel."""
        self.parent = parent
        self._create_widget()

    def _create_widget(self):
        """Create the preview panel widgets."""
        self.frame = ttk.Frame(self.parent, padding="5")
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        self.title_var = tk.StringVar(value="Preview")
        self.title_label = ttk.Label(self.frame, textvariable=self.title_var,
                                     font=("TkDefaultFont", 10, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.info_var = tk.StringVar(value="")
        self.info_label = ttk.Label(self.frame, textvariable=self.info_var,
                                    wraplength=300, justify="left")
        self.info_label.grid(row=1, column=0, sticky="nw", pady=(0, 4))

        self.content_text = tk.Text(self.frame, wrap="word", state="disabled",
                                    height=6, padx=4, pady=4)
        self.content_text.grid(row=2, column=0, sticky="nsew")
        self.frame.rowconfigure(2, weight=1)

        self.v_scrollbar = ttk.Scrollbar(self.frame, orient="vertical",
                                          command=self.content_text.yview)
        self.v_scrollbar.grid(row=2, column=1, sticky="ns")
        self.content_text.configure(yscrollcommand=self.v_scrollbar.set)

    def clear(self):
        """Clear the preview panel."""
        self.title_var.set("Preview")
        self.info_var.set("No selection")
        self._set_content("")

    def show_path(self, path):
        """Show preview for the given filesystem path."""
        if not path or not os.path.exists(path):
            self.clear()
            return

        name = os.path.basename(path)
        try:
            stat = os.stat(path)
            size = format_size(stat.st_size)
            modified = format_time(stat.st_mtime)
        except OSError:
            size = "?"
            modified = "?"

        if os.path.isdir(path):
            self.title_var.set(f"📁 {name}")
            try:
                count = len(os.listdir(path))
            except OSError:
                count = "?"
            self.info_var.set(f"Directory\n{count} items\n{modified}")
            self._set_content("")
            return

        # File
        file_type = get_file_type(type('E', (), {'is_dir': lambda s, **kw: False, 'name': name})())
        self.title_var.set(f"📄 {name}")
        self.info_var.set(f"{file_type}\n{size}\n{modified}")

        text = self._read_text_preview(path)
        if text is not None:
            lines = text.splitlines()
            if len(lines) > self.TEXT_MAX_LINES:
                text = "\n".join(lines[:self.TEXT_MAX_LINES]) + "\n…"
            self._set_content(text)
        else:
            self._set_content("[Binary file — no text preview]")

    def _read_text_preview(self, path):
        """Try to read a text preview of the file. Returns None if binary."""
        try:
            with open(path, "rb") as f:
                chunk = f.read(self.TEXT_PREVIEW_BYTES)
            if b"\x00" in chunk:
                return None
            encodings = ("utf-8", "latin-1", "cp1252")
            for enc in encodings:
                try:
                    return chunk.decode(enc)
                except UnicodeDecodeError:
                    continue
            return None
        except (OSError, PermissionError):
            return None

    def _set_content(self, text):
        """Set the content text widget text."""
        self.content_text.configure(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", text)
        self.content_text.configure(state="disabled")

    def set_theme_colors(self, bg, fg):
        """Apply theme colors to the text widget."""
        try:
            self.content_text.configure(bg=bg, fg=fg,
                                          insertbackground=fg,
                                          selectbackground=fg,
                                          selectforeground=bg)
        except Exception:
            pass
