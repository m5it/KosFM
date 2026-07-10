
"""
Navigation module for KosFM.
Handles directory navigation, tree expansion, and path management.
"""

import os
from tkinter import messagebox

from .utils.error_handler import handle_error


class NavigationManager:
    """Manages directory navigation and tree operations."""
    
    def __init__(self, app):
        """
        Initialize navigation manager.
        
        Args:
            app: KosFMApp instance for callbacks
        """
        self.app = app
        
    def navigate_to(self, path):
        """Navigate to a specific directory."""
        if not os.path.isdir(path):
            self.app.status_bar.update(f"Invalid directory: {path}")
            return
            
        self.app.status_bar.update(f"Loading: {path}")
        self.app.current_path = path
        self.app.file_panel.set_path(path)
        self.app.file_panel.set_current_path(path)
        self.app._refresh_file_view()
        
    def go_to_parent(self):
        """Navigate to parent directory."""
        try:
            if self.app.current_path:
                parent = os.path.dirname(self.app.current_path)
                if parent and parent != self.app.current_path:
                    self.navigate_to(parent)
        except Exception as e:
            self.app._show_error(f"Navigation error: {e}")
            
    def on_path_entry(self, event):
        """Handle path entry from path bar."""
        try:
            path = self.app.file_panel.path_var.get()
            if os.path.isdir(path):
                self.app.status_bar.update(f"Navigating to: {path}")
                self.navigate_to(path)
            else:
                messagebox.showerror("Error", f"Directory not found: {path}")
                self.app.status_bar.update("Directory not found")
        except Exception as e:
            self.app._show_error(f"Path entry error: {e}")
            
    @handle_error
    def populate_tree_roots(self):
        """Populate tree with root directories."""
        from .utils.platform_utils import get_root_directories
        
        roots = get_root_directories()
        for path, name in roots:
            has_children = self._has_subdirectories(path)
            self.app.tree_panel.insert_node("", path, name, has_children)
            
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
        
    def on_tree_expand(self, item, path):
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
                self.app.tree_panel.insert_node(item, full_path, name, has_children)
                
        except PermissionError:
            pass
        except OSError as e:
            print(f"Error loading directory {path}: {e}")
            
    def on_tree_select(self, event):
        """Handle tree selection."""
        try:
            item = self.app.tree_panel.get_selection()
            if not item:
                return
            path = self.app.tree_panel.get_item_path(item[0])
            if not path or not os.path.isdir(path):
                return
            self.navigate_to(path)
        except Exception as e:
            self.app._show_error(f"Tree selection error: {e}")
