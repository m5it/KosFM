#!/usr/bin/env python3
"""
KosFM Application
A simple file manager with tree view and file listing.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import platform
import traceback
from datetime import datetime

from config import (
    APP_NAME, WINDOW_SIZE, MIN_WINDOW_SIZE, 
    TREE_WIDTH, PANEL_PADDING, FOLDER_ICON, FILE_ICON,
    FILE_COLUMNS, SIZE_UNITS, DEFAULT_PATH
)


def handle_error(func):
    """Decorator for error handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PermissionError as e:
            args[0]._show_error(f"Permission denied: {e}")
        except FileNotFoundError as e:
            args[0]._show_error(f"File not found: {e}")
        except OSError as e:
            args[0]._show_error(f"System error: {e}")
        except Exception as e:
            args[0]._show_error(f"Unexpected error: {e}")
            traceback.print_exc()
    return wrapper


class KosFMApp:
    """Main application class for KosFM."""
    
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(*MIN_WINDOW_SIZE)
        
        self.current_path = None
        
        # View options
        self.show_hidden_files = tk.BooleanVar(value=False)
        self.show_status_bar = tk.BooleanVar(value=True)
        
        # Initialize UI components
        self.setup_ui()
        self.populate_tree_roots()
        
        # Set initial directory
        self.navigate_to(os.path.expanduser(DEFAULT_PATH))
        
    def _show_error(self, message):
        """Show error message in status bar or dialog."""
        print(f"Error: {message}")
        messagebox.showerror("Error", message)
        
    @handle_error
    def navigate_to(self, path):
        """Navigate to a specific directory."""
        if not os.path.isdir(path):
            self._update_status(f"Invalid directory: {path}")
            return
            
        self._update_status(f"Loading: {path}")
        self.current_path = path
        self._update_path_bar()
        self._refresh_file_view()
        
    def _update_path_bar(self):
        """Update the path bar with current directory."""
        if hasattr(self, 'path_var'):
            self.path_var.set(self.current_path or "")
        
    @handle_error
    def populate_tree_roots(self):
        """Populate tree with root directories based on platform."""
        system = platform.system()
        
        if system == "Windows":
            self._add_windows_drives()
        else:
            self._add_unix_roots()
            
    def _add_windows_drives(self):
        """Add Windows drive letters to tree."""
        import string
        from ctypes import windll
        
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive_path = f"{letter}:\\"
                self._insert_tree_node("", drive_path, drive_path, True)
            bitmask >>= 1
            
    def _add_unix_roots(self):
        """Add Unix root directories to tree."""
        self._insert_tree_node("", "/", "/", True)
        home = os.path.expanduser("~")
        home_name = os.path.basename(home) or "home"
        self._insert_tree_node("", home, home_name, True)
        
    @handle_error
    def _has_subdirectories(self, path):
        """Check if directory has any subdirectories."""
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        return True
        except (PermissionError, OSError):
            pass
        return False
        
    def _insert_tree_node(self, parent, path, text, is_dir):
        """Insert a node into the tree."""
        display_text = f"{FOLDER_ICON} {text}" if is_dir else text
        node_id = self.tree.insert(parent, "end", text=display_text, values=(path,), open=False)
        if is_dir and self._has_subdirectories(path):
            self.tree.insert(node_id, "end", text="dummy", values=("",))
        return node_id
        
    @handle_error
    def _on_tree_expand(self, event):
        """Handle tree node expansion - lazy load children."""
        item = self.tree.focus()
        if not item:
            return
        path = self.tree.item(item, "values")[0] if self.tree.item(item, "values") else ""
        if not path:
            return
        children = self.tree.get_children(item)
        if children and self.tree.item(children[0], "text") == "dummy":
            self.tree.delete(children[0])
            self._load_directory_children(item, path)
            
    def _load_directory_children(self, parent_item, path):
        """Load actual directory contents into tree."""
        try:
            dirs = []
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        dirs.append((entry.name, entry.path))
            dirs.sort(key=lambda x: x[0].lower())
            for name, full_path in dirs:
                self._insert_tree_node(parent_item, full_path, name, True)
        except PermissionError:
            pass
        except OSError as e:
            print(f"Error loading directory {path}: {e}")
            
    def _on_tree_select(self, event):
        """Handle tree selection - update file view."""
        try:
            item = self.tree.selection()
            if not item:
                return
            path = self.tree.item(item[0], "values")[0] if self.tree.item(item[0], "values") else ""
            if not path or not os.path.isdir(path):
                return
            self.navigate_to(path)
        except Exception as e:
            self._show_error(f"Tree selection error: {e}")
        
    def _refresh_file_view(self):
        """Refresh the file view with current directory contents."""
        try:
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            if not self.current_path:
                self._update_status("No directory selected")
                return
            entries = []
            with os.scandir(self.current_path) as it:
                for entry in it:
                    # Filter hidden files based on setting
                    if not self.show_hidden_files.get() and entry.name.startswith('.'):
                        continue
                    entries.append(entry)
            entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            
            file_count = 0
            dir_count = 0
            
            for entry in entries:
                try:
                    stat = entry.stat(follow_symlinks=False)
                    name = entry.name
                    display_name = f"{FOLDER_ICON} {name}" if entry.is_dir() else f"{FILE_ICON} {name}"
                    size = self._format_size(stat.st_size) if not entry.is_dir() else ""
                    modified = self._format_time(stat.st_mtime)
                    file_type = self._get_file_type(entry)
                    self.file_tree.insert("", "end", text=name, values=(display_name, size, modified, file_type))
                    
                    if entry.is_dir():
                        dir_count += 1
                    else:
                        file_count += 1
                        
                except (OSError, PermissionError):
                    continue
            
            # Update status bar
            total = file_count + dir_count
            self._update_status(f"{total} items ({dir_count} folders, {file_count} files) - {self.current_path}")
            
        except PermissionError:
            self.file_tree.insert("", "end", values=("Access Denied", "", "", ""))
            self._update_status("Permission denied")
        except OSError as e:
            self.file_tree.insert("", "end", values=(f"Error: {e}", "", "", ""))
            self._update_status(f"Error: {e}")
        
    def setup_ui(self):
        """Initialize the user interface."""
        # Create menu bar first
        self._create_menu_bar()
        
        # Main container with padding
        self.main_frame = ttk.Frame(self.root, padding=str(PANEL_PADDING))
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=3)
        self.main_frame.columnconfigure(0, weight=0)
        self.main_frame.rowconfigure(0, weight=1)
        self._create_tree_panel()
        self._create_file_panel()
        self._create_status_bar()
        
    def _create_menu_bar(self):
        """Create the menu bar with File, View, and Help menus."""
        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Create menus
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        
        # Add menus to menu bar
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        # Populate menus
        self._create_file_menu()
        self._create_view_menu()
        self._create_help_menu()
        
    def _create_file_menu(self):
        """Create File menu with Refresh and Exit options."""
        # Refresh option with keyboard shortcut
        self.file_menu.add_command(
            label="Refresh",
            command=self._refresh_file_view,
            accelerator="Ctrl+R"
        )
        self.root.bind("<Control-r>", lambda e: self._refresh_file_view())
        
        # Separator
        self.file_menu.add_separator()
        
        # Exit option with keyboard shortcut
        self.file_menu.add_command(
            label="Exit",
            command=self.root.destroy,
            accelerator="Ctrl+Q"
        )
        self.root.bind("<Control-q>", lambda e: self.root.destroy())
        
    def _create_view_menu(self):
        """Create View menu with display options."""
        # Show hidden files checkbox
        self.view_menu.add_checkbutton(
            label="Show Hidden Files",
            variable=self.show_hidden_files,
            command=self._toggle_hidden_files
        )
        
        # Separator
        self.view_menu.add_separator()
        
        # Show status bar checkbox
        self.view_menu.add_checkbutton(
            label="Show Status Bar",
            variable=self.show_status_bar,
            command=self._toggle_status_bar
        )
        
    def _toggle_hidden_files(self):
        """Toggle hidden files visibility and refresh view."""
        self._refresh_file_view()
        
    def _toggle_status_bar(self):
        """Toggle status bar visibility."""
        if self.show_status_bar.get():
            self.status_frame.grid()
        else:
            self.status_frame.grid_remove()
            
    def _create_help_menu(self):
        """Create Help menu with About and Shortcuts options."""
        # Keyboard shortcuts
        self.help_menu.add_command(
            label="Keyboard Shortcuts",
            command=self._show_shortcuts
        )
        
        # Separator
        self.help_menu.add_separator()
        
        # About
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
File → Refresh      Reload directory
File → Exit         Close application
View → Show Hidden Files    Toggle hidden files
View → Show Status Bar      Toggle status bar
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
        
    def _show_about(self):
        """Show About dialog."""
        about_text = f"""KosFM

Version: 1.1.0
A simple file manager with tree view and file listing.

Built with Python and tkinter.

Features:
• Dual-pane interface
• Lazy loading directory tree
• File details (size, date, type)
• Cross-platform support
"""
        messagebox.showinfo("About", about_text)
        
    def _create_tree_panel(self):
        """Create the left panel with directory tree."""
        self.tree_frame = ttk.Frame(self.main_frame)
        self.tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, PANEL_PADDING))
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(self.tree_frame, columns=("name",), selectmode="browse", show="tree")
        self.tree.heading("#0", text="Directory", anchor="w")
        self.tree.column("#0", width=TREE_WIDTH, minwidth=150, stretch=True)
        self.tree_scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewOpen>>", self._on_tree_expand)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
    def _create_file_panel(self):
        """Create the center panel for file listing with path bar."""
        self.file_frame = ttk.Frame(self.main_frame)
        self.file_frame.grid(row=0, column=1, sticky="nsew")
        self.file_frame.columnconfigure(0, weight=1)
        self.file_frame.rowconfigure(1, weight=1)
        self._create_path_bar()
        self._create_file_tree()
        
    def _create_path_bar(self):
        """Create the path bar showing current directory."""
        path_frame = ttk.Frame(self.file_frame)
        path_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        path_frame.columnconfigure(1, weight=1)
        self.up_btn = ttk.Button(path_frame, text="⬆ Up", width=6, command=self._go_to_parent)
        self.up_btn.grid(row=0, column=0, padx=(0, 5))
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        self.path_entry.grid(row=0, column=1, sticky="ew")
        self.path_entry.bind("<Return>", self._on_path_entry)
        self.refresh_btn = ttk.Button(path_frame, text="🔄 Refresh", width=10, command=self._refresh_file_view)
        self.refresh_btn.grid(row=0, column=2, padx=(5, 0))
        
    def _create_file_tree(self):
        """Create the file listing tree view."""
        tree_frame = ttk.Frame(self.file_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self.file_tree = ttk.Treeview(tree_frame, columns=FILE_COLUMNS, selectmode="browse", show="headings")
        self.file_tree.heading("name", text="Name", anchor="w")
        self.file_tree.heading("size", text="Size", anchor="e")
        self.file_tree.heading("modified", text="Modified", anchor="w")
        self.file_tree.heading("type", text="Type", anchor="w")
        self.file_tree.column("name", width=300, minwidth=150, stretch=True)
        self.file_tree.column("size", width=80, minwidth=60, stretch=False)
        self.file_tree.column("modified", width=150, minwidth=100, stretch=False)
        self.file_tree.column("type", width=80, minwidth=60, stretch=False)
        self.file_v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.file_tree.yview)
        self.file_h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=self.file_v_scrollbar.set, xscrollcommand=self.file_h_scrollbar.set)
        self.file_tree.grid(row=0, column=0, sticky="nsew")
        self.file_v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.file_tree.bind("<Double-1>", self._on_file_double_click)
        
    def _create_status_bar(self):
        """Create the status bar at the bottom."""
        self.status_frame = ttk.Frame(self.root, relief="sunken", padding="2")
        self.status_frame.grid(row=1, column=0, sticky="ew", padx=PANEL_PADDING, pady=(0, PANEL_PADDING))
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var, anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        
    def _update_status(self, message):
        """Update the status bar message."""
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def _go_to_parent(self):
        """Navigate to parent directory."""
        try:
            if self.current_path:
                parent = os.path.dirname(self.current_path)
                if parent and parent != self.current_path:
                    self.navigate_to(parent)
        except Exception as e:
            self._show_error(f"Navigation error: {e}")
                
    def _on_path_entry(self, event):
        """Handle path entry - navigate to entered path."""
        try:
            path = self.path_var.get()
            if os.path.isdir(path):
                self._update_status(f"Navigating to: {path}")
                self.navigate_to(path)
            else:
                messagebox.showerror("Error", f"Directory not found: {path}")
                self._update_status("Directory not found")
        except Exception as e:
            self._show_error(f"Path entry error: {e}")
            
    def _on_file_double_click(self, event):
        """Handle double-click on file - navigate if folder."""
        try:
            item = self.file_tree.selection()
            if not item:
                return
            values = self.file_tree.item(item[0], "values")
            if not values:
                return
            display_name = values[0]
            name = display_name.replace(f"{FOLDER_ICON} ", "").replace(f"{FILE_ICON} ", "")
            full_path = os.path.join(self.current_path, name)
            if os.path.isdir(full_path):
                self._update_status(f"Opening: {full_path}")
                self.navigate_to(full_path)
        except Exception as e:
            self._show_error(f"Double-click error: {e}")
        
    def _format_size(self, size):
        """Format file size in human-readable format."""
        for unit in SIZE_UNITS:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
        
    def _format_time(self, timestamp):
        """Format timestamp for display."""
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")
        
    def _get_file_type(self, entry):
        """Get file type description."""
        if entry.is_dir():
            return "Folder"
        else:
            name = entry.name
            if '.' in name:
                ext = name.rsplit('.', 1)[-1].upper()
                return f"{ext} File"
            return "File"
        
    def run(self):
        """Start the main event loop."""
        self.root.mainloop()


def main():
    """Application entry point."""
    try:
        root = tk.Tk()
        app = KosFMApp(root)
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
