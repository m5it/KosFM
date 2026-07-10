"""
Main application module for KosFM.
Wires together all UI components and utilities.
"""

import os
import sys
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

from .config import APP_NAME, WINDOW_SIZE, MIN_WINDOW_SIZE, TREE_WIDTH, DEFAULT_PATH
from .utils.config_manager import ConfigManager
from .utils.error_handler import handle_error
from .utils.file_utils import format_size, format_time, get_file_type
from .utils.platform_utils import get_root_directories
from .utils.xdg_mime import (
    get_mime_type,
    get_default_application,
    set_default_application,
    find_applications_for_mime_type,
    launch_application,
    open_file_with_default,
    parse_desktop_file
)
from .ui.tree_panel import TreePanel
from .ui.file_panel import FilePanel
from .ui.menu_bar import MenuBar
from .ui.status_bar import StatusBar
from .dialogs import OpenWithDialog, PropertiesDialog
from .navigation import NavigationManager


class KosFMApp:
    """Main application class for KosFM."""
    
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        
        # Initialize config manager
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # Initialize navigation manager
        self.nav = NavigationManager(self)
        
        # Clipboard for copy/paste operations
        self._clipboard = None
        
        # Apply saved window geometry
        self._apply_window_geometry()
        self.root.minsize(*MIN_WINDOW_SIZE)
        
        self.current_path = None
        self._sash_save_timer = None
        
        # Create UI
        self.setup_ui()
        
        # Bind to sash movement for saving position
        self._bind_sash_save()
        
        # Populate tree roots
        self.nav.populate_tree_roots()
        
        # Set initial directory
        self.nav.navigate_to(os.path.expanduser(DEFAULT_PATH))
        
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
        # Cancel any pending sash save timer
        if self._sash_save_timer:
            self.root.after_cancel(self._sash_save_timer)
            self._sash_save_timer = None
            self._save_sash_position()
        
        self._save_window_state()
        self.root.destroy()
        
    def _save_window_state(self):
        """Save current window state to config."""
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
            
        # Also save sash position as backup
        if hasattr(self, 'paned_window'):
            try:
                sash_pos = self.paned_window.sashpos(0)
                if "panel" not in self.config:
                    self.config["panel"] = {}
                self.config["panel"]["left_width"] = sash_pos
            except:
                pass
            
        self.config["view"]["show_hidden_files"] = self.menu_bar.get_show_hidden_var().get()
        self.config["view"]["show_status_bar"] = self.menu_bar.get_show_status_var().get()
        
        self.config_manager.save_config(self.config)
        
    def _bind_sash_save(self):
        """Bind to sash movement to save panel width."""
        self.paned_window.bind('<ButtonRelease-1>', self._on_sash_release)
        
    def _on_sash_release(self, event):
        """Handle sash release - save position after a delay."""
        if self._sash_save_timer:
            self.root.after_cancel(self._sash_save_timer)
        self._sash_save_timer = self.root.after(500, self._save_sash_position)
        
    def _save_sash_position(self):
        """Save the current sash position to config."""
        try:
            sash_pos = self.paned_window.sashpos(0)
            if "panel" not in self.config:
                self.config["panel"] = {}
            self.config["panel"]["left_width"] = sash_pos
            self.config_manager.save_config(self.config)
            print(f"Saved panel width: {sash_pos}")
        except Exception as e:
            print(f"Could not save sash position: {e}")
        finally:
            self._sash_save_timer = None
        
    def setup_ui(self):
        """Initialize the user interface."""
        self._create_menu_bar()
        
        self.main_frame = ttk.Frame(self.root, padding="5")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        self.paned_window = ttk.PanedWindow(self.main_frame, orient="horizontal")
        self.paned_window.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        self._create_tree_panel()
        self._create_file_panel()
        
        # Restore sash position after window is fully rendered
        if "panel" in self.config and "left_width" in self.config["panel"]:
            saved_width = self.config["panel"]["left_width"]
            self.root.after(100, lambda: self._restore_sash_position(saved_width))
        else:
            self.paned_window.sashpos(0, TREE_WIDTH)
        
        self._create_status_bar()
        
    def _restore_sash_position(self, width):
        """Restore sash position after window is rendered."""
        try:
            self.paned_window.sashpos(0, width)
            print(f"Restored panel width: {width}")
        except Exception as e:
            print(f"Could not restore sash position: {e}")
        
    def _create_menu_bar(self):
        """Create menu bar with handlers."""
        handlers = {
            'refresh': self._refresh_file_view,
            'exit': self.root.destroy,
            'toggle_hidden': self._toggle_hidden_files,
            'toggle_status': self._toggle_status_bar,
        }
        self.menu_bar = MenuBar(self.root, handlers)
        self.menu_bar.get_show_hidden_var().set(self.config["view"]["show_hidden_files"])
        self.menu_bar.get_show_status_var().set(self.config["view"]["show_status_bar"])
        
    def _create_tree_panel(self):
        """Create the tree panel."""
        self.tree_panel = TreePanel(
            self.paned_window,
            on_select_callback=self.nav.on_tree_select,
            on_expand_callback=self.nav.on_tree_expand
        )
        self.tree_panel.add_to_paned_window(weight=0)
        
    def _create_file_panel(self):
        """Create the file panel."""
        self.file_panel = FilePanel(
            self.paned_window,
            on_double_click_callback=self._on_file_double_click,
            on_file_click_callback=None,  # No single-click opening
            on_context_menu_callback=self._on_context_menu
        )
        self.file_panel.add_to_paned_window(weight=1)
        
        self.file_panel.bind_up_button(self.nav.go_to_parent)
        self.file_panel.bind_refresh_button(self._refresh_file_view)
        self.file_panel.bind_path_entry(self.nav.on_path_entry)
        
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
                
    def _open_file(self, path):
        """Open file with default application."""
        if not os.path.isfile(path):
            return
            
        mime_type = get_mime_type(path)
        saved_app = self.config.get("mime_apps", {}).get(mime_type)
        
        if saved_app:
            desktop_path = self._find_desktop_file(saved_app)
            if desktop_path:
                app_info = parse_desktop_file(desktop_path)
                if app_info:
                    self.status_bar.update(f"Opening: {path}")
                    launch_application(path, app_info)
                    return
        
        self.status_bar.update(f"Opening: {path}")
        open_file_with_default(path)
                
    def _find_desktop_file(self, desktop_name):
        """Find .desktop file by name."""
        search_dirs = [
            Path.home() / '.local' / 'share' / 'applications',
            Path('/usr/share/applications'),
            Path('/usr/local/share/applications'),
        ]
        for d in search_dirs:
            path = d / desktop_name
            if path.exists():
                return path
        return None
            
    def _on_context_menu(self, action, path):
        """Handle context menu actions."""
        if not path and action != "paste":
            return
            
        if action == "open":
            self._open_file(path)
        elif action == "open_with":
            dialog = OpenWithDialog(self.root, path, self.config_manager, 
                                   self.config, self.status_bar.update)
            dialog.show()
        elif action == "copy":
            self._on_context_copy(path)
        elif action == "paste":
            self._on_context_paste(path)
        elif action == "rename":
            self._on_context_rename(path)
        elif action == "remove":
            self._on_context_remove(path)
        elif action == "copy_path":
            self._copy_path_to_clipboard(path)
        elif action == "properties":
            dialog = PropertiesDialog(self.root, path)
            dialog.show()
            
    def _on_context_copy(self, path):
        """Copy file/directory to clipboard."""
        self._clipboard = path
        self.status_bar.update(f"Copied: {os.path.basename(path)}")
        
    def _on_context_paste(self, dest_dir):
        """Paste from clipboard to destination."""
        if not self._clipboard:
            self.status_bar.update("Nothing to paste")
            return
            
        if not os.path.exists(self._clipboard):
            self.status_bar.update("Source file no longer exists")
            self._clipboard = None
            return
            
        src_name = os.path.basename(self._clipboard)
        dest_path = os.path.join(dest_dir, src_name)
        
        # If destination exists, add number suffix
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(src_name)
            counter = 1
            while os.path.exists(dest_path):
                new_name = f"{base} ({counter}){ext}"
                dest_path = os.path.join(dest_dir, new_name)
                counter += 1
        
        try:
            if os.path.isdir(self._clipboard):
                shutil.copytree(self._clipboard, dest_path)
            else:
                shutil.copy2(self._clipboard, dest_path)
            self.status_bar.update(f"Pasted: {os.path.basename(dest_path)}")
            self._refresh_file_view()
        except Exception as e:
            self._show_error(f"Could not paste: {e}")
            
    def _on_context_rename(self, path):
        """Rename file or directory."""
        if not path:
            return
            
        old_name = os.path.basename(path)
        new_name = simpledialog.askstring("Rename", f"Rename '{old_name}' to:", 
                                          initialvalue=old_name)
        if not new_name or new_name == old_name:
            return
            
        new_path = os.path.join(os.path.dirname(path), new_name)
        
        if os.path.exists(new_path):
            self._show_error(f"Cannot rename: '{new_name}' already exists")
            return
            
        try:
            os.rename(path, new_path)
            self.status_bar.update(f"Renamed: {old_name} -> {new_name}")
            self._refresh_file_view()
        except Exception as e:
            self._show_error(f"Could not rename: {e}")
            
    def _on_context_remove(self, path):
        """Remove file or directory with confirmation."""
        if not path:
            return
            
        name = os.path.basename(path)
        is_dir = os.path.isdir(path)
        
        item_type = "directory" if is_dir else "file"
        response = messagebox.askyesno("Confirm Delete", 
                                       f"Are you sure you want to delete {item_type} '{name}'?\n\n"
                                       f"This action cannot be undone.")
        if not response:
            return
            
        try:
            if is_dir:
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.status_bar.update(f"Deleted: {name}")
            self._refresh_file_view()
        except Exception as e:
            self._show_error(f"Could not delete: {e}")
            
    def _copy_path_to_clipboard(self, path):
        """Copy file path to clipboard."""
        self.root.clipboard_clear()
        self.root.clipboard_append(path)
        self.status_bar.update(f"Copied to clipboard: {path}")
        
    def _toggle_hidden_files(self):
        """Toggle hidden files visibility."""
        self._refresh_file_view()
        
    def _toggle_status_bar(self):
        """Toggle status bar visibility."""
        if self.menu_bar.get_show_status_var().get():
            self.status_bar.show()
        else:
            self.status_bar.hide()
            
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
                self.nav.navigate_to(full_path)
            else:
                # Open file on double-click
                self._open_file(full_path)
        except Exception as e:
            self._show_error(f"Double-click error: {e}")
            
    def run(self):
        """Start the main event loop."""
        self.root.mainloop()
