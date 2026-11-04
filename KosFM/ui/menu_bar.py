
"""
Menu bar widget for KosFM.
Creates File, Edit, View, and Help menus.
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
                - focus_search: Called for Search / Filter
                - new_folder: Called for New Folder
                - new_file: Called for New File
                - add_bookmark: Called for Add Bookmark
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
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)

        # Add to menu bar
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        # Populate menus
        self._create_file_menu()
        self._create_edit_menu()
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
        
        self.file_menu.add_command(
            label="New Folder",
            command=self.handlers.get('new_folder'),
            accelerator="Ctrl+Shift+N"
        )
        self.root.bind("<Control-Shift-N>", lambda e: self.handlers.get('new_folder', lambda: None)())

        self.file_menu.add_command(
            label="New File",
            command=self.handlers.get('new_file'),
            accelerator="Ctrl+N"
        )
        self.root.bind("<Control-n>", lambda e: self.handlers.get('new_file', lambda: None)())

        self.file_menu.add_separator()

        self.file_menu.add_command(
            label="Exit",
            command=self.handlers.get('exit'),
            accelerator="Ctrl+Q"
        )
        self.root.bind("<Control-q>", lambda e: self.handlers.get('exit', lambda: None)())
        
    def _create_edit_menu(self):
        """Create Edit menu."""
        self.edit_menu.add_command(
            label="Search / Filter",
            command=self.handlers.get('focus_search'),
            accelerator="Ctrl+F"
        )
        self.root.bind("<Control-f>", lambda e: self.handlers.get('focus_search', lambda: None)())

        self.edit_menu.add_separator()

        self.edit_menu.add_command(
            label="Add Bookmark",
            command=self.handlers.get('add_bookmark'),
            accelerator="Ctrl+D"
        )
        self.root.bind("<Control-d>", lambda e: self.handlers.get('add_bookmark', lambda: None)())

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
Ctrl+N      New file
Ctrl+Shift+N  New folder
Ctrl+F      Focus search box
Ctrl+D      Add current directory to bookmarks
Esc         Clear search

Navigation:
Double-click    Open folder
Enter           Navigate to path (in path bar)

Menu:
File -> Refresh        Reload directory
File -> New Folder     Create new folder
File -> New File       Create new empty file
File -> Exit           Close application
Edit -> Search / Filter    Focus search box
Edit -> Add Bookmark       Bookmark current directory
View -> Show Hidden Files    Toggle hidden files
View -> Show Status Bar      Toggle status bar
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
        
    def _show_about(self):
        """Show About dialog."""
        from ..config import APP_NAME
        
        from ..config import APP_VERSION

        about_text = f"""{APP_NAME}

Version: {APP_VERSION}
A simple, cross-platform file manager built with Python and tkinter.

Features:
- Dual-pane interface with resizable panels
- File operations (Copy, Paste, Rename, Remove, New File/Folder)
- Linux xdg-mime integration for file associations
- "Open With" dialog with application selection
- Search / filter in current folder or recursively
- Bookmarks / favorites sidebar
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
