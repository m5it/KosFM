"""
Main application module for KosFM.
Wires together all UI components and utilities.
"""

import logging
import os
import sys
import shutil
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

logger = logging.getLogger(__name__)

from .config import APP_NAME, WINDOW_SIZE, MIN_WINDOW_SIZE, TREE_WIDTH, DEFAULT_PATH
from .utils.config_manager import ConfigManager
from .utils.error_handler import handle_error
from .utils.file_utils import format_size, format_time, get_file_type
from .utils.platform_utils import get_root_directories
from .utils.archive_handler import ARCHIVE_EXTENSIONS, create_archive, extract_archive
from .utils.search import walk_search
from .utils.theme import ThemeManager
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

        # Initialize theme manager
        self.theme_manager = ThemeManager(self.root)

        # Initialize navigation manager
        self.nav = NavigationManager(self)
        
        # Clipboard for copy/paste operations
        self._clipboard = None
        
        # Apply saved window geometry
        self._apply_window_geometry()
        self.root.minsize(*MIN_WINDOW_SIZE)
        
        self.current_path = None
        self._sash_save_timer = None
        self._right_sash_save_timer = None
        self._sort_column = "name"
        self._sort_reverse = False
        self._theme = self.config.get("theme", "light")
        self._show_preview = self.config.get("view", {}).get("show_preview_panel", True)
        self._preview_height = self.config.get("panel", {}).get("preview_height", 120)
        self._preview_sash_save_timer = None
        self._show_thumbnails = self.config.get("thumbnails", {}).get("enabled", True)

        # Search state
        self._cached_entries = []  # last scandir entries for filtering
        self._filter_query = ""
        self._filter_timer = None
        self._search_thread = None
        self._search_cancel = None
        self._search_active = False  # True when showing recursive results
        
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
        # Cancel any pending sash save timers
        if self._sash_save_timer:
            self.root.after_cancel(self._sash_save_timer)
            self._sash_save_timer = None
            self._save_sash_position()
        if self._right_sash_save_timer:
            self.root.after_cancel(self._right_sash_save_timer)
            self._right_sash_save_timer = None
            self._save_right_sash_position()
        if self._preview_sash_save_timer:
            self.root.after_cancel(self._preview_sash_save_timer)
            self._preview_sash_save_timer = None
            self._save_preview_sash_position()

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
            
        # Also save sash positions as backup
        if hasattr(self, 'paned_window'):
            try:
                sash_pos = self.paned_window.sashpos(0)
                if "panel" not in self.config:
                    self.config["panel"] = {}
                self.config["panel"]["left_width"] = sash_pos
            except:
                pass
        if hasattr(self, 'file_panel'):
            try:
                right_sash = self.file_panel.get_controls_height()
                if right_sash is not None:
                    if "panel" not in self.config:
                        self.config["panel"] = {}
                    self.config["panel"]["right_top_height"] = right_sash
                preview_sash = self.file_panel.get_preview_height()
                if preview_sash is not None:
                    self.config["panel"]["preview_height"] = preview_sash
            except:
                pass

        self.config["view"]["show_hidden_files"] = self.menu_bar.get_show_hidden_var().get()
        self.config["view"]["show_status_bar"] = self.menu_bar.get_show_status_var().get()
        self.config["view"]["show_preview_panel"] = self.menu_bar.get_show_preview_var().get()
        if "thumbnails" not in self.config:
            self.config["thumbnails"] = {}
        self.config["thumbnails"]["enabled"] = self.menu_bar.get_show_thumbnails_var().get()

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
        """Save the current left/right sash position to config."""
        try:
            sash_pos = self.paned_window.sashpos(0)
            if "panel" not in self.config:
                self.config["panel"] = {}
            self.config["panel"]["left_width"] = sash_pos
            self.config_manager.save_config(self.config)
            logger.debug("Saved panel width: %s", sash_pos)
        except Exception as e:
            logger.debug("Could not save sash position: %s", e)
        finally:
            self._sash_save_timer = None

    def _on_right_sash_released(self, event=None):
        """Handle vertical sash release in file panel."""
        if self._right_sash_save_timer:
            self.root.after_cancel(self._right_sash_save_timer)
        self._right_sash_save_timer = self.root.after(500, self._save_right_sash_position)

    def _on_sort_changed(self, column, reverse):
        """Handle sort column/direction change from file panel."""
        self._sort_column = column
        self._sort_reverse = reverse
        if "sort" not in self.config:
            self.config["sort"] = {}
        self.config["sort"]["column"] = column
        self.config["sort"]["reverse"] = reverse
        self.config_manager.save_config(self.config)
        self._render_entries(self._cached_entries, self._filter_query)

    def _save_right_sash_position(self):
        """Save the current file-panel vertical sash position."""
        try:
            height = self.file_panel.get_controls_height()
            if height is not None:
                if "panel" not in self.config:
                    self.config["panel"] = {}
                self.config["panel"]["right_top_height"] = height
                self.config_manager.save_config(self.config)
                logger.debug("Saved right panel top height: %s", height)
        except Exception as e:
            logger.debug("Could not save right sash position: %s", e)
        finally:
            self._right_sash_save_timer = None

    def _apply_theme(self, theme_name):
        """Apply theme and recursively update menu colors."""
        self.theme_manager.apply(theme_name)
        colors = self.theme_manager.get_colors(theme_name)

        # Update menu colors manually (ttk styles don't affect tk.Menu)
        if hasattr(self, 'menu_bar'):
            for menu in (self.menu_bar.file_menu, self.menu_bar.edit_menu,
                         self.menu_bar.view_menu, self.menu_bar.help_menu,
                         self.menu_bar.menu_bar):
                try:
                    menu.configure(bg=colors["menu_bg"], fg=colors["fg"])
                except Exception:
                    pass
        if hasattr(self, 'status_bar'):
            try:
                self.status_bar.set_theme_colors(colors["status_bg"], colors["fg"])
            except Exception:
                pass
        if hasattr(self, 'tree_panel'):
            try:
                self.tree_panel.set_theme_colors(colors["tree_bg"], colors["fg"])
            except Exception:
                pass
        if hasattr(self, 'file_panel'):
            try:
                self.file_panel.set_theme_colors(colors["tree_bg"], colors["fg"])
            except Exception:
                pass

    def _toggle_theme(self):
        """Toggle between light and dark theme."""
        new_theme = "dark" if self._theme == "light" else "light"
        self._theme = new_theme
        self.config["theme"] = new_theme
        self.config_manager.save_config(self.config)
        self._apply_theme(new_theme)
        self.status_bar.update(f"Theme: {new_theme}")

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
        self._create_status_bar()

        # Apply theme now that all widgets (including menus and status bar) exist.
        self._apply_theme(self._theme)

    def _load_bookmarks(self):
        """Load bookmarks from config and add to tree panel."""
        self.tree_panel.clear_bookmarks()
        for path in self.config.get("bookmarks", []):
            if os.path.isdir(path):
                label = os.path.basename(path) or path
                self.tree_panel.add_bookmark_node(path, label)
        
        # Restore horizontal sash position after window is fully rendered
        if "panel" in self.config and "left_width" in self.config["panel"]:
            saved_width = self.config["panel"]["left_width"]
            self.root.after(100, lambda: self._restore_sash_position(saved_width))
        else:
            self.paned_window.sashpos(0, TREE_WIDTH)

        # Restore vertical sash position in file panel
        if "panel" in self.config and "right_top_height" in self.config["panel"]:
            saved_height = self.config["panel"]["right_top_height"]
            self.root.after(150, lambda: self._restore_right_sash_position(saved_height))

    def _restore_sash_position(self, width):
        """Restore horizontal sash position after window is rendered."""
        try:
            self.paned_window.sashpos(0, width)
            logger.debug("Restored panel width: %s", width)
        except Exception as e:
            logger.debug("Could not restore sash position: %s", e)

    def _restore_right_sash_position(self, height):
        """Restore vertical sash position in file panel."""
        try:
            self.file_panel.set_controls_height(height)
            logger.debug("Restored right panel top height: %s", height)
        except Exception as e:
            logger.debug("Could not restore right sash position: %s", e)
        
    def _create_menu_bar(self):
        """Create menu bar with handlers."""
        handlers = {
            'refresh': self._refresh_file_view,
            'exit': self.root.destroy,
            'toggle_hidden': self._toggle_hidden_files,
            'toggle_status': self._toggle_status_bar,
            'toggle_preview': self._toggle_preview_panel,
            'toggle_thumbnails': self._toggle_thumbnails,
            'toggle_theme': self._toggle_theme,
            'focus_search': self._focus_search,
            'new_folder': self._on_new_folder,
            'new_file': self._on_new_file,
            'add_bookmark': self._add_bookmark,
        }
        self.menu_bar = MenuBar(self.root, handlers)
        self.menu_bar.get_show_hidden_var().set(self.config["view"]["show_hidden_files"])
        self.menu_bar.get_show_status_var().set(self.config["view"]["show_status_bar"])
        self.menu_bar.get_show_preview_var().set(self._show_preview)
        self.menu_bar.get_show_thumbnails_var().set(self._show_thumbnails)
        # Ensure menu bar handlers dict matches actual methods (defensive)
        assert 'add_bookmark' in handlers
        
    def _create_tree_panel(self):
        """Create the tree panel."""
        self.tree_panel = TreePanel(
            self.paned_window,
            on_select_callback=self._on_tree_select,
            on_expand_callback=self.nav.on_tree_expand,
            on_bookmark_select=self._on_bookmark_select
        )
        self.tree_panel.add_to_paned_window(weight=0)
        self._load_bookmarks()
        
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
        self.file_panel.set_search_callbacks(
            on_change=self._on_filter_changed,
            on_recursive=self._on_recursive_search
        )
        self.file_panel.set_selection_change_callback(self._update_status_for_selection)
        self.file_panel.bind_sash_change(self._on_right_sash_released)
        self.file_panel.set_sort_callbacks(self._on_sort_changed)

        # Apply saved sort preferences
        sort_cfg = self.config.get("sort", {})
        self._sort_column = sort_cfg.get("column", "name")
        self._sort_reverse = sort_cfg.get("reverse", False)
        self.file_panel._sort_column = self._sort_column
        self.file_panel._sort_reverse = self._sort_reverse
        self.file_panel._update_sort_indicators()

        # Wire preview panel and thumbnails
        self.file_panel.bind_preview_sash_change(self._on_preview_sash_released)
        self.file_panel.show_preview(self._show_preview)
        if self._show_preview and self._preview_height:
            self.root.after(200, lambda: self.file_panel.set_preview_height(self._preview_height))
        self.file_panel.set_thumbnails_enabled(self._show_thumbnails)
        # Global keyboard shortcuts
        # Global keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self._on_new_file())
        self.root.bind("<Control-N>", lambda e: self._on_new_file())
        self.root.bind("<Control-Shift-N>", lambda e: self._on_new_folder())
        self.root.bind("<Control-d>", lambda e: self._add_bookmark())
        self.root.bind("<Control-D>", lambda e: self._add_bookmark())
        self.root.bind("<F5>", lambda e: self._refresh_file_view())
        self.root.bind("<Escape>", self._on_escape)
        
    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = StatusBar(self.root)
        if not self.config["view"]["show_status_bar"]:
            self.status_bar.hide()
            
    def _show_error(self, message):
        """Show error message."""
        logger.error("%s", message)
        messagebox.showerror("Error", message)
        
    # ---- Search / filter ----

    def _focus_search(self, event=None):
        self.file_panel.focus_search()
        return "break"

    def _on_tree_select(self, event):
        """Handle tree selection: bookmark vs normal directory."""
        try:
            item = self.tree_panel.get_selection()
            if not item:
                return
            iid = item[0]
            if self.tree_panel.is_bookmark_node(iid):
                path = self.tree_panel.get_item_path(iid)
                if path and os.path.isdir(path):
                    self.nav.navigate_to(path)
                return
            # Normal directory
            path = self.tree_panel.get_item_path(iid)
            if not path or not os.path.isdir(path):
                return
            self.nav.navigate_to(path)
        except Exception as e:
            self._show_error(f"Tree selection error: {e}")

    def _on_bookmark_select(self, action, path):
        """Callback for bookmark interactions from tree panel."""
        if action == "remove":
            self._remove_bookmark(path)

    def _add_bookmark(self, path=None):
        """Add current directory to bookmarks."""
        path = path or self.current_path
        if not path or not os.path.isdir(path):
            self._show_error("No directory selected")
            return
        bookmarks = self.config.setdefault("bookmarks", [])
        if path in bookmarks:
            self.status_bar.update(f"Already bookmarked: {path}")
            return
        bookmarks.append(path)
        self.config_manager.save_config(self.config)
        label = os.path.basename(path) or path
        self.tree_panel.add_bookmark_node(path, label)
        self.status_bar.update(f"Bookmarked: {label}")

    def _remove_bookmark(self, path):
        """Remove a bookmark path from config and tree."""
        bookmarks = self.config.setdefault("bookmarks", [])
        if path in bookmarks:
            bookmarks.remove(path)
            self.config_manager.save_config(self.config)
        self.tree_panel.remove_bookmark_node(path)
        self.status_bar.update(f"Removed bookmark: {os.path.basename(path) or path}")

    def _on_escape(self, event=None):
        if self._search_active or self.file_panel.get_search_query():
            self._cancel_search()
            self.file_panel.clear_search()
            self._refresh_file_view()

    def _cancel_search(self):
        if self._search_cancel:
            self._search_cancel.set()
        self._search_active = False
        self._search_thread = None
        self._search_cancel = None

    def _on_filter_changed(self, query):
        """Debounced inline filter for current directory."""
        self._filter_query = query or ""
        # Cancel any recursive search
        if self._search_active:
            self._cancel_search()
        if self._filter_timer:
            self.root.after_cancel(self._filter_timer)
        # Small debounce so typing feels instant but not janky
        self._filter_timer = self.root.after(150, self._apply_filter)

    def _apply_filter(self):
        self._filter_timer = None
        if not self._search_active:
            self._render_entries(self._cached_entries, self._filter_query)

    def _on_recursive_search(self, query):
        """Start recursive search under current_path."""
        if not query or not self.current_path:
            return
        self._cancel_search()
        self._filter_query = query
        self._search_active = True
        self.file_panel.clear()  # clear view before results
        self.status_bar.update(f"Searching for '{query}' in {self.current_path} ...")

        cancel = threading.Event()
        self._search_cancel = cancel

        def on_batch(batch):
            # Schedule UI update on main thread
            self.root.after(0, lambda b=batch: self._append_search_results(b, query))

        def worker():
            show_hidden = self.menu_bar.get_show_hidden_var().get()
            total = walk_search(
                self.current_path, query,
                show_hidden=show_hidden,
                cancel_event=cancel,
                on_batch=on_batch,
            )
            self.root.after(0, lambda t=total: self._finish_search(t, query, cancelled=cancel.is_set()))

        t = threading.Thread(target=worker, daemon=True)
        self._search_thread = t
        t.start()

    def _append_search_results(self, batch, query):
        if not self._search_active:
            return
        for item in batch:
            name = item['name']
            display_name = f"📁 {name}" if item['is_dir'] else f"📄 {name}"
            size = "" if item['is_dir'] else format_size(item['size'])
            modified = format_time(item['mtime'])
            file_type = "Folder" if item['is_dir'] else get_file_type(
                type('E', (), {'is_dir': lambda s, **kw: False, 'name': name})()
            )
            # Show relative path as type hint for recursive results
            rel = os.path.relpath(item['path'], self.current_path) if self.current_path else item['path']
            # Insert with full path stored in item text for navigation
            iid = self.file_panel.insert_item(item['path'], display_name, size, modified, os.path.dirname(rel) or ".")
            # Tag to allow navigation: we store full path
            _ = iid
        # Update count in status
        count = len(self.file_panel.tree.get_children())
        self.status_bar.update(f"Found {count} matches for '{query}' — {self.current_path} (recursive)")

    def _finish_search(self, total, query, cancelled=False):
        if not self._search_active and not cancelled:
            return
        if cancelled:
            self.status_bar.update(f"Search cancelled — {len(self.file_panel.tree.get_children())} matches for '{query}'")
        else:
            self.status_bar.update(f"Found {total} matches for '{query}' in {self.current_path} (recursive)")
        self._search_thread = None

    def _render_entries(self, entries, query=""):
        """Render entries to file panel, applying optional name filter and sort."""
        self.file_panel.clear()
        if query:
            entries = [e for e in entries if query.lower() in e.name.lower()]
        entries_sorted = self._sort_entries(entries)
        file_count = 0
        dir_count = 0
        for entry in entries_sorted:
            try:
                stat = entry.stat(follow_symlinks=False)
                name = entry.name
                display_name = f"📁 {name}" if entry.is_dir() else f"📄 {name}"
                size = format_size(stat.st_size) if not entry.is_dir() else ""
                modified = format_time(stat.st_mtime)
                file_type = get_file_type(entry)
                thumbnail = None
                if hasattr(entry, 'path') and not entry.is_dir():
                    thumbnail = self.file_panel.get_thumbnail(entry.path)
                self.file_panel.insert_item(name, display_name, size, modified, file_type, thumbnail)
                if entry.is_dir():
                    dir_count += 1
                else:
                    file_count += 1
            except (OSError, PermissionError):
                continue
        total = file_count + dir_count
        base = self.current_path or ""
        if query:
            shown = total
            self.status_bar.update(f"{shown} / {len(self._cached_entries)} matches for '{query}' — {base}")
            if shown == 0:
                self.file_panel.insert_item("", f"No matches for '{query}'", "", "", "")
        else:
            self.status_bar.update(f"{total} items ({dir_count} folders, {file_count} files) - {base}")

    def _update_status_for_selection(self):
        """Update status bar and preview panel based on selection."""
        selected = self.file_panel.tree.selection()
        if len(selected) == 1:
            path = self._resolve_item_path(selected[0])
            self._update_preview(path)
            return

        self._update_preview(None)
        if len(selected) <= 1:
            return
        total_size = 0
        valid = 0
        for iid in selected:
            path = self._resolve_item_path(iid)
            if path and os.path.exists(path):
                try:
                    if os.path.isfile(path):
                        total_size += os.path.getsize(path)
                    valid += 1
                except OSError:
                    pass
        self.status_bar.update(f"{len(selected)} items selected ({format_size(total_size)})")

    def _update_preview(self, path):
        """Update preview panel for the given path (or clear if None)."""
        if not self._show_preview:
            return
        if hasattr(self.file_panel, 'preview_panel'):
            if path:
                self.file_panel.preview_panel.show_path(path)
            else:
                self.file_panel.preview_panel.clear()

    def _sort_entries(self, entries):
        """Sort entries according to current sort column and direction."""
        col = self._sort_column
        reverse = self._sort_reverse

        def _key(entry):
            try:
                stat = entry.stat(follow_symlinks=False)
            except OSError:
                stat = None

            if col == "name":
                # Folders first when sorting by name, then alphabetical
                return (not entry.is_dir(), entry.name.lower())
            elif col == "size":
                size = stat.st_size if stat else 0
                return size
            elif col == "modified":
                mtime = stat.st_mtime if stat else 0
                return mtime
            elif col == "type":
                return get_file_type(entry).lower()
            return entry.name.lower()

        # For non-name columns, separate folders/files to keep folders first
        if col != "name":
            dirs = [e for e in entries if e.is_dir()]
            files = [e for e in entries if not e.is_dir()]
            dirs_sorted = sorted(dirs, key=_key, reverse=reverse)
            files_sorted = sorted(files, key=_key, reverse=reverse)
            return dirs_sorted + files_sorted

        return sorted(entries, key=_key, reverse=reverse)

    @handle_error
    def _refresh_file_view(self):
        """Refresh the file view (caches entries, applies current filter)."""
        try:
            if not self.current_path:
                self.status_bar.update("No directory selected")
                return

            # If a recursive search is active, cancel it and return to normal view
            if self._search_active:
                self._cancel_search()

            entries = []
            with os.scandir(self.current_path) as it:
                for entry in it:
                    if not self.menu_bar.get_show_hidden_var().get() and entry.name.startswith('.'):
                        continue
                    entries.append(entry)

            self._cached_entries = entries
            self._render_entries(entries, self._filter_query)

        except PermissionError:
            self._cached_entries = []
            self.file_panel.clear()
            self.file_panel.insert_item("", "Access Denied", "", "", "")
            self.status_bar.update("Permission denied")
        except OSError as e:
            self._cached_entries = []
            self.file_panel.clear()
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
        elif action == "new_folder":
            self._on_new_folder(path)
        elif action == "new_file":
            self._on_new_file(path)
        elif action == "go_to_parent":
            self.nav.go_to_parent()
        elif action == "extract_archive":
            self._on_context_extract_archive(path)
        elif action == "create_archive":
            self._on_context_create_archive(path)

    def _on_context_copy(self, path):
        """Copy file/directory or multi-selection to clipboard."""
        selected = self.file_panel.tree.selection()
        if len(selected) > 1:
            paths = [self._resolve_item_path(iid) for iid in selected]
            paths = [p for p in paths if p]
            self._clipboard = paths
            self.status_bar.update(f"Copied {len(paths)} items")
        elif path:
            self._clipboard = path
            self.status_bar.update(f"Copied: {os.path.basename(path)}")
        else:
            self.status_bar.update("Nothing selected")

    def _on_context_paste(self, dest_dir):
        """Paste from clipboard to destination."""
        if not self._clipboard:
            self.status_bar.update("Nothing to paste")
            return

        if isinstance(self._clipboard, list):
            # Multi-selection paste
            pasted = 0
            skipped = 0
            for src in self._clipboard:
                if not os.path.exists(src):
                    skipped += 1
                    continue
                dest_path = self._unique_dest_path(dest_dir, os.path.basename(src))
                try:
                    if os.path.isdir(src):
                        shutil.copytree(src, dest_path)
                    else:
                        shutil.copy2(src, dest_path)
                    pasted += 1
                except Exception as e:
                    self._show_error(f"Could not paste {src}: {e}")
            self.status_bar.update(f"Pasted {pasted} items ({skipped} skipped)")
            self._refresh_file_view()
            return

        if not os.path.exists(self._clipboard):
            self.status_bar.update("Source file no longer exists")
            self._clipboard = None
            return

        dest_path = self._unique_dest_path(dest_dir, os.path.basename(self._clipboard))
        try:
            if os.path.isdir(self._clipboard):
                shutil.copytree(self._clipboard, dest_path)
            else:
                shutil.copy2(self._clipboard, dest_path)
            self.status_bar.update(f"Pasted: {os.path.basename(dest_path)}")
            self._refresh_file_view()
        except Exception as e:
            self._show_error(f"Could not paste: {e}")

    def _unique_dest_path(self, dest_dir, src_name):
        """Generate unique destination path, adding suffix if needed."""
        dest_path = os.path.join(dest_dir, src_name)
        if not os.path.exists(dest_path):
            return dest_path
        base, ext = os.path.splitext(src_name)
        counter = 1
        while os.path.exists(dest_path):
            new_name = f"{base} ({counter}){ext}"
            dest_path = os.path.join(dest_dir, new_name)
            counter += 1
        return dest_path
            
    def _on_new_folder(self, target_dir=None):
        """Create a new folder in current directory."""
        target_dir = target_dir or self.current_path
        if not target_dir or not os.path.isdir(target_dir):
            self._show_error("No directory selected")
            return

        name = simpledialog.askstring("New Folder", "Folder name:", initialvalue="New Folder")
        if not name:
            return

        # Sanitize name to avoid path traversal / invalid chars
        name = name.replace(os.sep, "_").replace("/", "_")
        if not name:
            self._show_error("Invalid folder name")
            return

        new_path = os.path.join(target_dir, name)
        if os.path.exists(new_path):
            self._show_error(f"Cannot create: '{name}' already exists")
            return

        try:
            os.mkdir(new_path)
            self.status_bar.update(f"Created folder: {name}")
            self._refresh_file_view()
        except Exception as e:
            self._show_error(f"Could not create folder: {e}")

    def _on_new_file(self, target_dir=None):
        """Create a new empty file in current directory."""
        target_dir = target_dir or self.current_path
        if not target_dir or not os.path.isdir(target_dir):
            self._show_error("No directory selected")
            return

        name = simpledialog.askstring("New File", "File name:", initialvalue="new_file.txt")
        if not name:
            return

        # Sanitize name
        name = name.replace(os.sep, "_").replace("/", "_")
        if not name:
            self._show_error("Invalid file name")
            return

        new_path = os.path.join(target_dir, name)
        if os.path.exists(new_path):
            self._show_error(f"Cannot create: '{name}' already exists")
            return

        try:
            with open(new_path, "w", encoding="utf-8") as f:
                pass
            self.status_bar.update(f"Created file: {name}")
            self._refresh_file_view()
        except Exception as e:
            self._show_error(f"Could not create file: {e}")

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
            
    def _on_context_extract_archive(self, path):
        """Extract selected archive into current directory."""
        if not path or not os.path.isfile(path):
            self.status_bar.update("No archive selected")
            return
        dest_dir = self.current_path
        if not dest_dir:
            self.status_bar.update("No destination directory")
            return
        try:
            extract_archive(path, dest_dir)
            self.status_bar.update(f"Extracted: {os.path.basename(path)}")
            self._refresh_file_view()
        except Exception as e:
            self._show_error(f"Could not extract archive: {e}")

    def _on_context_create_archive(self, paths):
        """Create an archive from selected items in the current directory."""
        if not paths:
            self.status_bar.update("Nothing selected")
            return
        dest_dir = self.current_path
        if not dest_dir:
            self.status_bar.update("No destination directory")
            return

        # Default archive name
        if len(paths) == 1:
            base = os.path.basename(paths[0])
            default_name = f"{base}.zip"
        else:
            default_name = "archive.zip"

        name = simpledialog.askstring("Create Archive", "Archive name:", initialvalue=default_name)
        if not name:
            return
        name = name.replace(os.sep, "_").replace("/", "_").strip()
        if not name:
            self._show_error("Invalid archive name")
            return

        if not any(name.lower().endswith(ext) for ext in ARCHIVE_EXTENSIONS):
            name += ".zip"

        dest_path = self._unique_dest_path(dest_dir, name)
        try:
            create_archive(paths, dest_path)
            self.status_bar.update(f"Created archive: {os.path.basename(dest_path)}")
            self._refresh_file_view()
        except Exception as e:
            self._show_error(f"Could not create archive: {e}")

    def _on_context_remove(self, path):
        """Remove selected item(s) with confirmation."""
        selected = self.file_panel.tree.selection()
        if len(selected) > 1:
            paths = [self._resolve_item_path(iid) for iid in selected]
            paths = [p for p in paths if p]
            if not paths:
                return
            response = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete {len(paths)} selected items?\n\n"
                f"This action cannot be undone."
            )
            if not response:
                return
            deleted = 0
            failed = []
            for p in paths:
                try:
                    if os.path.isdir(p):
                        shutil.rmtree(p)
                    else:
                        os.remove(p)
                    deleted += 1
                except Exception as e:
                    failed.append(f"{os.path.basename(p)}: {e}")
            self.status_bar.update(f"Deleted {deleted} items")
            self._refresh_file_view()
            if failed:
                self._show_error("Some items could not be deleted:\n" + "\n".join(failed))
            return

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

    def _toggle_preview_panel(self):
        """Toggle preview panel visibility."""
        self._show_preview = self.menu_bar.get_show_preview_var().get()
        self.file_panel.show_preview(self._show_preview)
        if self._show_preview and self._preview_height:
            self.root.after(100, lambda: self.file_panel.set_preview_height(self._preview_height))
        self.config["view"]["show_preview_panel"] = self._show_preview
        self.config_manager.save_config(self.config)

    def _toggle_thumbnails(self):
        """Toggle image thumbnails in the file list."""
        self._show_thumbnails = self.menu_bar.get_show_thumbnails_var().get()
        self.file_panel.set_thumbnails_enabled(self._show_thumbnails)
        if "thumbnails" not in self.config:
            self.config["thumbnails"] = {}
        self.config["thumbnails"]["enabled"] = self._show_thumbnails
        self.config_manager.save_config(self.config)
        self._refresh_file_view()
        self.status_bar.update(f"Thumbnails: {'on' if self._show_thumbnails else 'off'}")

    def _on_preview_sash_released(self, event=None):
        """Handle preview panel sash release - save position after a delay."""
        if self._preview_sash_save_timer:
            self.root.after_cancel(self._preview_sash_save_timer)
        self._preview_sash_save_timer = self.root.after(500, self._save_preview_sash_position)

    def _save_preview_sash_position(self):
        """Save the current preview pane height."""
        try:
            height = self.file_panel.get_preview_height()
            if height is not None:
                if "panel" not in self.config:
                    self.config["panel"] = {}
                self.config["panel"]["preview_height"] = height
                self.config_manager.save_config(self.config)
                logger.debug("Saved preview height: %s", height)
        except Exception as e:
            logger.debug("Could not save preview height: %s", e)
        finally:
            self._preview_sash_save_timer = None

    def _resolve_selected_path(self):
        """Resolve selected item to full filesystem path, handling search results."""
        item = self.file_panel.get_selection()
        if not item:
            return None
        iid = item[0]
        # In recursive search mode, Treeview text holds the full path
        text = self.file_panel.tree.item(iid, "text")
        if text and os.path.isabs(text):
            return text
        values = self.file_panel.get_item_values(iid)
        if not values:
            return None
        display_name = values[0]
        name = display_name.replace("📁 ", "").replace("📄 ", "")
        if not name:
            return None
        return os.path.join(self.current_path, name) if self.current_path else None

    def _on_file_double_click(self, event):
        """Handle double-click on file."""
        try:
            full_path = self._resolve_selected_path()
            if not full_path:
                return
            if os.path.isdir(full_path):
                # Exit search view when navigating via double-click
                if self._search_active:
                    self._cancel_search()
                    self.file_panel.clear_search()
                self.status_bar.update(f"Opening: {full_path}")
                self.nav.navigate_to(full_path)
            else:
                self._open_file(full_path)
        except Exception as e:
            self._show_error(f"Double-click error: {e}")
            
    def run(self):
        """Start the main event loop."""
        self.root.mainloop()
