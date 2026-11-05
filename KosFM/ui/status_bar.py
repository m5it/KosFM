"""
Status bar widget for KosFM.
Displays status messages at the bottom of the window.
"""

import tkinter as tk
from tkinter import ttk

from ..config import PANEL_PADDING


class StatusBar:
    """Status bar widget."""
    
    def __init__(self, root):
        """
        Initialize status bar.
        
        Args:
            root: Root window
        """
        self.root = root
        self._create_widget()
        
    def _create_widget(self):
        """Create the status bar widget."""
        self.frame = ttk.Frame(self.root, relief="sunken", padding="2")
        self.frame.grid(row=1, column=0, sticky="ew", padx=PANEL_PADDING, pady=(0, PANEL_PADDING))

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")

        self.label = ttk.Label(self.frame, textvariable=self.status_var, anchor="w")
        self.label.pack(side="left", fill="x", expand=True)

    def set_theme_colors(self, bg, fg):
        """Update status bar background/foreground (tk.Menu compatibility)."""
        try:
            self.frame.configure(style="StatusBar.TFrame")
            self._style = ttk.Style(self.frame)
            self._style.configure("StatusBar.TFrame", background=bg)
            self.label.configure(background=bg, foreground=fg)
        except Exception:
            pass
        
    def update(self, message):
        """
        Update status bar message.
        
        Args:
            message: Message to display
        """
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def show(self):
        """Show the status bar."""
        self.frame.grid(row=1, column=0, sticky="ew", padx=PANEL_PADDING, pady=(0, PANEL_PADDING))
        
    def hide(self):
        """Hide the status bar."""
        self.frame.grid_remove()
        
    def is_visible(self):
        """Check if status bar is visible."""
        return self.frame.winfo_viewable()
