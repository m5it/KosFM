"""
Main application module for KosFM.
Wires together all UI components and utilities.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox

from .config import APP_NAME, WINDOW_SIZE, MIN_WINDOW_SIZE, TREE_WIDTH, DEFAULT_PATH
from .utils.config_manager import ConfigManager
from .utils.error_handler import handle_error
from .utils.file_utils import format_size, format_time, get_file_type
from .utils.platform_utils import get_root_directories
from .ui.tree_panel import TreePanel
from .ui.file_panel import FilePanel
from .ui.menu_bar import MenuBar
from .ui.status_bar import StatusBar


class KosFMApp:
    """Main application class for KosFM."""
    
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        
        # Initialize config manager
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # Apply saved window geometry
        self._apply_window_geometry()
        self.root.minsize(*MIN_WINDOW_SIZE)
        
        self.current_path = None
        
        # Create UI
        self.setup_ui()
        
        # Populate tree roots
        self.populate_tree_roots()
        
        # Set initial directory
        self.navigate_to(os.path.expanduser(DEFAULT_PATH))
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
    def _apply_window_geometry(self):
        """Apply saved window position and size."""
        width = self.config["window"]["width"]
        height = self.config["window"]["height"]
        x = self.config["window"]["x"]
        y = self.config["window"]["y"]
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def _on_window_close(self):
        """Handle window close event."""
        self._save_window_state()
        self.root.destroy()
        
    def _save_window_state(self):
        """Save current window state to config."""
        # Get window geometry
        geometry = self.root.geometry()
        try:
            size, x, y = geometry.split('+')
            width, height = size.split('x')
            self.config["window"]["width"] = int(width)
            self.config["window"]["height"] = int(height)
            self.config["window"]["x"] = int(x)
            self.config["window"]["y"] = int(y)
        except ValueError:
            pass
            
        # Save panel width
        if hasattr(self, 'paned_window'):
            try:
                sash_pos = self.paned_window.sashpos(0)
                self.config["panel"]["left_width"] = sash_pos
            except:
                pass
                
        # Save view options
        self.config["view"]["show_hidden_files"] = self.menu_bar.get_show_hidden_var().get()
        self.config["view"]["show_status_bar"] = self.menu_bar.get_show_status_var().get()
        
        # Save to file
        self.config_manager.save_config(self.config)
        
    def setup_ui(self):
        """Initialize the user interface."""
        # Create menu bar
        self._create_menu_bar()
        
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="5")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create paned window for resizable panels
        self.paned_window = ttk.PanedWindow(self.main_frame, orient="horizontal")
        self.paned_window.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        # Create panels
        self._create_tree_panel()
        self._create_file_panel()
        
        # Set initial sash position
        if "panel" in self.config and "left_width" in self.config["panel"]:
            self.paned_window.sashpos(0, self.config["panel"]["left_width"])
        else:
            self.paned_window.sashpos(0, TREE_WIDTH)
        
        # Create status bar
        self._create_status_bar()
        
    def _create_menu_bar(self):
        """Create menu bar with handlers."""
        handlers = {
            'refresh': self._refresh_file_view,
            'exit': self.root.destroy,
            'toggle_hidden': self._toggle_hidden_files,
            'toggle_status': self._toggle_status_bar,
        }
        self.menu_bar = MenuBar(self.root, handlers)
        
        # Apply saved view options
        self.menu_bar.get_show_hidden_var().set(self.config["view"]["show_hidden_files"])
        self.menu_bar.get_show_status_var().set(self.config["view"]["show_status_bar"])
        
    def _create_tree_panel(self):
        """Create the tree panel."""
        self.tree_panel = TreePanel(
            self.paned_window,
            on_select_callback=self._on_tree_select,
            on_expand_callback=self._on_tree_expand
        )
        self.tree_panel.add_to_paned_window(weight=0)
        
    def _create_file_panel(self):
        """Create the file panel."""
        self.file_panel = FilePanel(
            self.paned_window,
            on_double_click_callback=self._on_file_double_click
        )
        self.file_panel.add_to_paned_window(weight=1)
        
        # Bind controls
        self.file_panel.bind_up_button(self._go_to_parent)
        self.file_panel.bind_refresh_button(self._refresh_file_view)
        self.file_panel.bind_path_entry(self._on_path_entry)
        
    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = StatusBar(self.root)
        if not self.config["view"]["show_status_bar"]:
            self.status_bar.hide()
            
    def _show_error(self, message):
        """Show error message."""
        print(f"Error: {message}")
        messagebox.showerror("Error", message)
        
    @handle_error
    def navigate_to(self, path):
        """Navigate to a specific directory."""
        if not os.path.isdir(path):
            self.status_bar.update(f"Invalid directory: {path}")
            return
            
        self.status_bar.update(f"Loading: {path}")
        self.current_path = path
        self.file_panel.set_path(path)
        self._refresh_file_view()
        
    @handle_error
    def populate_tree_roots(self):
        """Populate tree with root directories."""
        roots = get_root_directories()
        for path, name in roots:
            has_children = self._has_subdirectories(path)
            self.tree_panel.insert_node("", path, name, has_children)
            
    def _has_subdirectories(self, path):
        """Check if directory has subdirectories."""
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        return True
        except (PermissionError, OSError):
            pass
        return False
        
    def _on_tree_expand(self, item, path):
        """Handle tree node expansion."""
        try:
            dirs = []
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        has_children = self._has_subdirectories(entry.path)
                        dirs.append((entry.name, entry.path, has_children))
                        
            dirs.sort(key=lambda x: x[0].lower())
            
            for name, full_path, has_children in dirs:
                self.tree_panel.insert_node(item, full_path, name, has_children)
                
        except PermissionError:
            pass
        except OSError as e:
            print(f"Error loading directory {path}: {e}")
            
    def _on_tree_select(self, event):
        """Handle tree selection."""
        try:
            item = self.tree_panel.get_selection()
            if not item:
                return
            path = self.tree_panel.get_item_path(item[0])
            if not path or not os.path.isdir(path):
                return
            self.navigate_to(path)
        except Exception as e:
            self._show_error(f"Tree selection error: {e}")
            
    def _refresh_file_view(self):
        """Refresh the file view."""
        try:
            self.file_panel.clear()
            
            if not self.current_path:
                self.status_bar.update("No directory selected")
                return
                
            entries = []
            with os.scandir(self.current_path) as it:
                for entry in it:
                    # Filter hidden files
                    if not self.menu_bar.get_show_hidden_var().get() and entry.name.startswith('.'):
                        continue
                    entries.append(entry)
                    
            entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            
            file_count = 0
            dir_count = 0
            
            for entry in entries:
                try:
                    stat = entry.stat(follow_symlinks=False)
                    name = entry.name
                    display_name = f"📁 {name}" if entry.is_dir() else f"📄 {name}"
                    size = format_size(stat.st_size) if not entry.is_dir() else ""
                    modified = format_time(stat.st_mtime)
                    file_type = get_file_type(entry)
                    
                    self.file_panel.insert_item(name, display_name, size, modified, file_type)
                    
                    if entry.is_dir():
                        dir_count += 1
                    else:
                        file_count += 1
                        
                except (OSError, PermissionError):
                    continue
                    
            total = file_count + dir_count
            self.status_bar.update(f"{total} items ({dir_count} folders, {file_count} files) - {self.current_path}")
            
        except PermissionError:
            self.file_panel.insert_item("", "Access Denied", "", "", "")
            self.status_bar.update("Permission denied")
        except OSError as e:
            self.file_panel.insert_item("", f"Error: {e}", "", "", "")
            self.status_bar.update(f"Error: {e}")
            
    def _toggle_hidden_files(self):
        """Toggle hidden files visibility."""
        self._refresh_file_view()
        
    def _toggle_status_bar(self):
        """Toggle status bar visibility."""
        if self.menu_bar.get_show_status_var().get():
            self.status_bar.show()
        else:
            self.status_bar.hide()
            
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
        """Handle path entry."""
        try:
            path = self.file_panel.path_var.get()
            if os.path.isdir(path):
                self.status_bar.update(f"Navigating to: {path}")
                self.navigate_to(path)
            else:
                messagebox.showerror("Error", f"Directory not found: {path}")
                self.status_bar.update("Directory not found")
        except Exception as e:
            self._show_error(f"Path entry error: {e}")
            
    def _on_file_double_click(self, event):
        """Handle double-click on file."""
        try:
            item = self.file_panel.get_selection()
            if not item:
                return
            values = self.file_panel.get_item_values(item[0])
            if not values:
                return
            display_name = values[0]
            name = display_name.replace("📁 ", "").replace("📄 ", "")
            full_path = os.path.join(self.current_path, name)
            if os.path.isdir(full_path):
                self.status_bar.update(f"Opening: {full_path}")
                self.navigate_to(full_path)
        except Exception as e:
            self._show_error(f"Double-click error: {e}")
            
    def run(self):
        """Start the main event loop."""
        self.root.mainloop()
