
"""
Menu bar widget for KosFM.
Creates File, View, and Help menus.
"""

import tkinter as tk
from tkinter import messagebox


class MenuBar:
    """Application menu bar."""
    
    def __init__(self, root, handlers):
        """
        Initialize menu bar.
        
        Args:
            root: Root window
            handlers: Dict with callback functions for menu items
                - refresh: Called for Refresh
                - exit: Called for Exit
                - toggle_hidden: Called for Show Hidden Files
                - toggle_status: Called for Show Status Bar
                - show_shortcuts: Called for Keyboard Shortcuts
                - show_about: Called for About
        """
        self.root = root
        self.handlers = handlers
        
        self._create_menus()
        
    def _create_menus(self):
        """Create menu bar and menus."""
        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Create menus
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        
        # Add to menu bar
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        # Populate menus
        self._create_file_menu()
        self._create_view_menu()
        self._create_help_menu()
        
    def _create_file_menu(self):
        """Create File menu."""
        self.file_menu.add_command(
            label="Refresh",
            command=self.handlers.get('refresh'),
            accelerator="Ctrl+R"
        )
        self.root.bind("<Control-r>", lambda e: self.handlers.get('refresh', lambda: None)())
        
        self.file_menu.add_separator()
        
        self.file_menu.add_command(
            label="Exit",
            command=self.handlers.get('exit'),
            accelerator="Ctrl+Q"
        )
        self.root.bind("<Control-q>", lambda e: self.handlers.get('exit', lambda: None)())
        
    def _create_view_menu(self):
        """Create View menu."""
        self.show_hidden_var = tk.BooleanVar(value=False)
        self.show_status_var = tk.BooleanVar(value=True)
        
        self.view_menu.add_checkbutton(
            label="Show Hidden Files",
            variable=self.show_hidden_var,
            command=self.handlers.get('toggle_hidden')
        )
        
        self.view_menu.add_separator()
        
        self.view_menu.add_checkbutton(
            label="Show Status Bar",
            variable=self.show_status_var,
            command=self.handlers.get('toggle_status')
        )
        
    def _create_help_menu(self):
        """Create Help menu."""
        self.help_menu.add_command(
            label="Keyboard Shortcuts",
            command=self._show_shortcuts
        )
        
        self.help_menu.add_separator()
        
        self.help_menu.add_command(
            label="About",
            command=self._show_about
        )
        
    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts = """Keyboard Shortcuts:

Ctrl+R      Refresh current directory
Ctrl+Q      Exit application

Navigation:
Double-click    Open folder
Enter           Navigate to path (in path bar)

Menu:
File -> Refresh      Reload directory
File -> Exit         Close application
View -> Show Hidden Files    Toggle hidden files
View -> Show Status Bar      Toggle status bar
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
        
    def _show_about(self):
        """Show About dialog."""
        from ..config import APP_NAME
        
        about_text = f"""{APP_NAME}

Version: 1.4.0
A simple, cross-platform file manager built with Python and tkinter.

Features:
- Dual-pane interface with resizable panels
- File operations (Copy, Paste, Rename, Remove)
- Linux xdg-mime integration for file associations
- "Open With" dialog with application selection
- Context menu with file operations
- Lazy loading directory tree
- File details (size, date, type)
- Panel width persistence
- Cross-platform support (Linux, Windows, macOS)

For more information, see README.md
"""
        messagebox.showinfo(f"About {APP_NAME}", about_text)
        
    def get_show_hidden_var(self):
        """Get Show Hidden Files variable."""
        return self.show_hidden_var
        
    def get_show_status_var(self):
        """Get Show Status Bar variable."""
        return self.show_status_var
