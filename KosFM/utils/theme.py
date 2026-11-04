"""
Theme manager for KosFM.
Provides dark/light ttk styles.
"""

from tkinter import ttk


class ThemeManager:
    """Manages application color themes."""

    THEMES = {
        "light": {
            "bg": "#f0f0f0",
            "fg": "#000000",
            "tree_bg": "#ffffff",
            "tree_fg": "#000000",
            "tree_selected_bg": "#0078d7",
            "tree_selected_fg": "#ffffff",
            "entry_bg": "#ffffff",
            "status_bg": "#e0e0e0",
            "menu_bg": "#f0f0f0",
        },
        "dark": {
            "bg": "#2b2b2b",
            "fg": "#e0e0e0",
            "tree_bg": "#1e1e1e",
            "tree_fg": "#e0e0e0",
            "tree_selected_bg": "#094771",
            "tree_selected_fg": "#ffffff",
            "entry_bg": "#3c3c3c",
            "status_bg": "#333333",
            "menu_bg": "#2b2b2b",
        },
    }

    def __init__(self, root):
        self.root = root
        self._style = ttk.Style(root)
        self._current = "light"

    def apply(self, theme_name):
        """Apply a named theme (light or dark)."""
        if theme_name not in self.THEMES:
            theme_name = "light"
        self._current = theme_name
        colors = self.THEMES[theme_name]

        self.root.configure(bg=colors["bg"])

        # TButton
        self._style.configure("TButton", background=colors["bg"], foreground=colors["fg"])
        self._style.map("TButton",
                         background=[("active", colors["tree_selected_bg"])],
                         foreground=[("active", colors["tree_selected_fg"])])

        # TEntry
        self._style.configure("TEntry", fieldbackground=colors["entry_bg"], foreground=colors["fg"])

        # TFrame
        self._style.configure("TFrame", background=colors["bg"])

        # TLabelframe
        self._style.configure("TLabelframe", background=colors["bg"])
        self._style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["fg"])

        # Treeview
        self._style.configure("Treeview",
                              background=colors["tree_bg"],
                              foreground=colors["tree_fg"],
                              fieldbackground=colors["tree_bg"])
        self._style.configure("Treeview.Heading",
                              background=colors["status_bg"],
                              foreground=colors["fg"],
                              relief="flat")
        self._style.map("Treeview",
                        background=[("selected", colors["tree_selected_bg"])],
                        foreground=[("selected", colors["tree_selected_fg"])])

        # TPanedwindow
        self._style.configure("TPanedwindow", background=colors["bg"])

    def get_colors(self, theme_name=None):
        """Return color dict for a theme (defaults to current)."""
        return self.THEMES.get(theme_name or self._current, self.THEMES["light"])

    def get_current(self):
        return self._current
