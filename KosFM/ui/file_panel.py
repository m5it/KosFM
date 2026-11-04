
"""
File panel widget for KosFM.
Displays file listing with details.
"""

import os
import tkinter as tk
from tkinter import ttk

from ..config import FILE_COLUMNS, PANEL_PADDING
from ..utils.thumbnail_cache import ThumbnailCache
from .preview_panel import PreviewPanel


class FilePanel:
    """File listing panel widget."""
    
    def __init__(self, parent, on_double_click_callback, on_file_click_callback=None, 
                 on_context_menu_callback=None):
        """
        Initialize file panel.
        
        Args:
            parent: Parent widget (PanedWindow)
            on_double_click_callback: Function to call on double-click
            on_file_click_callback: Function to call on file single-click
            on_context_menu_callback: Function to call for context menu
        """
        self.parent = parent
        self.on_double_click = on_double_click_callback
        self.on_file_click = on_file_click_callback
        self.on_context_menu = on_context_menu_callback
        self.on_selection_change = None
        self._on_sort_change = None
        self._thumbnails_enabled = False
        self._thumbnail_cache = None

        self._create_widget()
        self._create_context_menu()
        
    def _create_widget(self):
        """Create the file panel widget."""
        # Create frame for file panel
        self.frame = ttk.Frame(self.parent)

        # Configure grid so paned window fills file panel
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        # Create the vertical paned window splitting top controls / file tree
        self._create_vertical_paned()

        # Create path bar
        self._create_path_bar()

        # Create search bar
        self._create_search_bar()

        # Create file tree and preview panel
        self._create_file_tree()
        self._create_preview_panel()

        # Add top-controls frame and tree frame to the paned window
        self._add_panes()

    def _create_vertical_paned(self):
        """Create the vertical PanedWindow that splits controls from file list."""
        self.v_paned = ttk.PanedWindow(self.frame, orient="vertical")
        self.v_paned.grid(row=0, column=0, sticky="nsew")

        self.controls_frame = ttk.Frame(self.v_paned)
        self.tree_frame_container = ttk.Frame(self.v_paned)

    def _add_panes(self):
        """Add controls and tree frames to the vertical paned window."""
        self.v_paned.add(self.controls_frame, weight=0)
        self.v_paned.add(self.tree_frame_container, weight=1)

    def _create_path_bar(self):
        """Create the path bar."""
        self.path_frame = ttk.Frame(self.controls_frame)
        self.path_frame.pack(fill="x", pady=(0, 3))
        self.path_frame.columnconfigure(1, weight=1)
        
        # Up button
        self.up_btn = ttk.Button(self.path_frame, text="⬆ Up", width=6)
        self.up_btn.grid(row=0, column=0, padx=(0, 5))
        
        # Path entry
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(self.path_frame, textvariable=self.path_var)
        self.path_entry.grid(row=0, column=1, sticky="ew")
        
        # Refresh button
        self.refresh_btn = ttk.Button(self.path_frame, text="🔄 Refresh", width=10)
        self.refresh_btn.grid(row=0, column=2, padx=(5, 0))
        
    def _create_file_tree(self):
        """Create the file listing tree inside a horizontal paned window."""
        self.h_paned = ttk.PanedWindow(self.tree_frame_container, orient="vertical")
        self.h_paned.pack(fill="both", expand=True)

        tree_frame = ttk.Frame(self.h_paned)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=FILE_COLUMNS,
            selectmode="extended",
            show="headings"
        )
        
        # Sort state
        self._sort_column = "name"
        self._sort_reverse = False
        self._sort_indicators = {}

        # Configure columns
        self._base_headings = {
            "name": "Name",
            "size": "Size",
            "modified": "Modified",
            "type": "Type",
        }
        for col in FILE_COLUMNS:
            self.tree.heading(col, text=self._base_headings[col], anchor="w" if col in ("name", "modified", "type") else "e")
            self.tree.heading(col, command=lambda c=col: self._on_header_click(c))

        self.tree.column("name", width=300, minwidth=150, stretch=True)
        self.tree.column("size", width=80, minwidth=60, stretch=False)
        self.tree.column("modified", width=150, minwidth=100, stretch=False)
        self.tree.column("type", width=80, minwidth=60, stretch=False)

        # Image column for thumbnails (only visible when enabled)
        self.tree.column("#0", width=0, minwidth=0, stretch=False)
        self.tree.heading("#0", text="")

        # Scrollbars
        self.v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")

        self.h_paned.add(tree_frame, weight=1)

        # Bind events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-1>", self._on_single_click)
        self.tree.bind("<Button-3>", self._on_right_click)  # Right-click

        # Track selection anchor and notify app after clicks
        self._selection_anchor = None
        def _track_and_update(event=None):
            self._track_anchor(event)
            if self.on_selection_change:
                self.on_selection_change()
        self.tree.bind("<Button-1>", _track_and_update, add="+")

        # Keyboard navigation
        def _key_nav_with_update(handler):
            def wrapper(event=None):
                result = handler(event)
                if self.on_selection_change:
                    self.on_selection_change()
                return result
            return wrapper

        self.tree.bind("<Up>", _key_nav_with_update(self._on_key_up))
        self.tree.bind("<Down>", _key_nav_with_update(self._on_key_down))
        self.tree.bind("<Return>", self._on_key_return)
        self.tree.bind("<KP_Enter>", self._on_key_return)
        self.tree.bind("<BackSpace>", self._on_key_backspace)
        self.tree.bind("<Delete>", _key_nav_with_update(self._on_key_delete))
        self.tree.bind("<F2>", self._on_key_rename)

    def _create_preview_panel(self):
        """Create the preview panel below the file tree."""
        self.preview_panel = PreviewPanel(self.h_paned)
        self.h_paned.add(self.preview_panel.frame, weight=0)

    def _create_search_bar(self):
        """Create the search/filter bar."""
        self.search_frame = ttk.Frame(self.controls_frame)
        self.search_frame.pack(fill="x")
        self.search_frame.columnconfigure(1, weight=1)

        ttk.Label(self.search_frame, text="🔍").grid(row=0, column=0, padx=(0, 4))

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew")



        self.search_clear_btn = ttk.Button(self.search_frame, text="✕", width=3,
                                           command=self._on_search_clear)
        self.search_clear_btn.grid(row=0, column=2, padx=(4, 0))

        self.recursive_var = tk.BooleanVar(value=False)
        self.recursive_check = ttk.Checkbutton(self.search_frame, text="Recursive",
                                               variable=self.recursive_var,
                                               command=self._on_recursive_toggle)
        self.recursive_check.grid(row=0, column=3, padx=(6, 0))

        self.search_placeholder = "Filter in folder..."
        self._search_has_placeholder = False
        self._set_search_placeholder()

        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<Escape>", self._on_search_escape)

        # Callbacks set by app
        self._on_search_change = None
        self._on_search_recursive = None
        self.search_var.trace_add("write", self._on_search_var_changed)

    def _set_search_placeholder(self):
        self.search_entry.insert(0, self.search_placeholder)
        self.search_entry.configure(foreground="gray")
        self._search_has_placeholder = True

    def _clear_search_placeholder(self):
        if self._search_has_placeholder:
            self.search_var.set("")
            self.search_entry.configure(foreground="")
            self._search_has_placeholder = False

    def _on_search_focus_in(self, event=None):
        self._clear_search_placeholder()

    def _on_search_focus_out(self, event=None):
        if not self.search_var.get():
            self._set_search_placeholder()

    def _on_search_escape(self, event=None):
        self.clear_search()
        return "break"

    def _on_search_clear(self):
        self.clear_search()

    def _on_recursive_toggle(self):
        if self.recursive_var.get():
            # Trigger recursive search if there's a query
            q = self.get_search_query()
            if q and self._on_search_recursive:
                self._on_search_recursive(q)
        else:
            # Back to filter mode
            q = self.get_search_query()
            if self._on_search_change:
                self._on_search_change(q)

    def _on_search_var_changed(self, *args):
        if self._search_has_placeholder:
            return
        if self.recursive_var.get():
            return  # recursive mode triggered explicitly, not on keystroke
        if self._on_search_change:
            self._on_search_change(self.search_var.get())

    def get_search_query(self):
        if self._search_has_placeholder:
            return ""
        return self.search_var.get().strip()

    def clear_search(self):
        self.recursive_var.set(False)
        self.search_var.set("")
        self.search_entry.configure(foreground="")
        self._search_has_placeholder = False
        self._set_search_placeholder()
        # notify to restore full listing
        if self._on_search_change:
            self._on_search_change("")

    def is_recursive(self):
        return self.recursive_var.get()

    def set_search_callbacks(self, on_change, on_recursive):
        """Register search callbacks from app."""
        self._on_search_change = on_change
        self._on_search_recursive = on_recursive

    def set_selection_change_callback(self, callback):
        """Register callback fired whenever tree selection changes."""
        self.on_selection_change = callback

    def set_controls_height(self, height):
        """Set height of the top controls pane (vertical sash position)."""
        try:
            if self.v_paned.winfo_exists():
                self.v_paned.sashpos(0, height)
        except Exception:
            pass

    def get_controls_height(self):
        """Return current top-controls pane height."""
        try:
            if self.v_paned.winfo_exists():
                return self.v_paned.sashpos(0)
        except Exception:
            pass
        return None

    def bind_sash_change(self, callback):
        """Bind a callback called when the vertical sash is released."""
        self.v_paned.bind("<ButtonRelease-1>", lambda e: callback())

    def bind_preview_sash_change(self, callback):
        """Bind a callback called when the preview horizontal sash is released."""
        self.h_paned.bind("<ButtonRelease-1>", lambda e: callback())

    def _on_header_click(self, column):
        """Handle click on a column header to sort."""
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = False
        self._update_sort_indicators()
        if self._on_sort_change:
            self._on_sort_change(self._sort_column, self._sort_reverse)

    def _update_sort_indicators(self):
        """Update header text with sort direction arrows."""
        indicator = "▲" if not self._sort_reverse else "▼"
        for col in FILE_COLUMNS:
            base = self._base_headings[col]
            if col == self._sort_column:
                self.tree.heading(col, text=f"{indicator} {base}")
            else:
                self.tree.heading(col, text=base)

    def set_sort_callbacks(self, callback):
        """Register callback when sort column/direction changes."""
        self._on_sort_change = callback

    def set_theme_colors(self, bg, fg):
        """Apply theme colors to internal non-ttk widgets (context menu)."""
        if hasattr(self, 'context_menu'):
            try:
                self.context_menu.configure(bg=bg, fg=fg)
            except Exception:
                pass
        if hasattr(self, 'preview_panel'):
            try:
                self.preview_panel.set_theme_colors(bg, fg)
            except Exception:
                pass

    def show_preview(self, show=True):
        """Show or hide the preview panel."""
        if not hasattr(self, 'preview_panel'):
            return
        try:
            if show:
                self.h_paned.add(self.preview_panel.frame, weight=0)
            else:
                self.h_paned.remove(self.preview_panel.frame)
        except Exception:
            pass

    def set_preview_height(self, height):
        """Set the preview pane height (horizontal sash position)."""
        try:
            if self.h_paned.winfo_exists():
                self.h_paned.sashpos(0, height)
        except Exception:
            pass

    def get_preview_height(self):
        """Return current preview pane height."""
        try:
            if self.h_paned.winfo_exists():
                return self.h_paned.sashpos(0)
        except Exception:
            pass
        return None

    def focus_search(self):
        self.search_entry.focus_set()
        if self._search_has_placeholder:
            self._clear_search_placeholder()

    def set_thumbnails_enabled(self, enabled):
        """Enable or disable image thumbnails."""
        self._thumbnails_enabled = bool(enabled)
        if self._thumbnails_enabled and self._thumbnail_cache is None:
            self._thumbnail_cache = ThumbnailCache()
        if not self._thumbnails_enabled:
            self._thumbnail_cache = None

    def get_thumbnail(self, path):
        """Return a cached thumbnail PhotoImage or None."""
        if not self._thumbnails_enabled or self._thumbnail_cache is None:
            return None
        return self._thumbnail_cache.get_thumbnail(path)

    def _create_context_menu(self):
        """Create right-click context menu."""
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Open", command=self._on_context_open)
        self.context_menu.add_command(label="Open With...", command=self._on_context_open_with)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="New Folder", command=self._on_context_new_folder)
        self.context_menu.add_command(label="New File", command=self._on_context_new_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy", command=self._on_context_copy)
        self.context_menu.add_command(label="Paste", command=self._on_context_paste)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Rename", command=self._on_context_rename)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Remove", command=self._on_context_remove)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Extract Archive", command=self._on_context_extract_archive)
        self.context_menu.add_command(label="Create Archive...", command=self._on_context_create_archive)

    def _on_single_click(self, event):
        """Handle single click with Ctrl/Shift multi-select support."""
        self.context_menu.unpost()

        item = self.tree.identify_row(event.y)
        if not item:
            return

        ctrl = (event.state & 0x0004) != 0
        shift = (event.state & 0x0001) != 0

        if ctrl:
            if item in self.tree.selection():
                self.tree.selection_remove(item)
            else:
                self.tree.selection_add(item)
            self.tree.focus(item)
            self._selection_anchor = item
        elif shift:
            anchor = self._selection_anchor or self.tree.focus()
            if anchor and anchor != item:
                all_items = self.tree.get_children("")
                try:
                    idx1 = all_items.index(anchor)
                    idx2 = all_items.index(item)
                except ValueError:
                    idx1 = idx2 = -1
                if idx1 >= 0 and idx2 >= 0:
                    start, end = sorted((idx1, idx2))
                    self.tree.selection_set(all_items[start:end + 1])
            else:
                self.tree.selection_set(item)
                self._selection_anchor = item
            self.tree.focus(item)
        else:
            self.tree.selection_set(item)
            self.tree.focus(item)
            self._selection_anchor = item
            if self.on_file_click:
                values = self.tree.item(item, "values")
                if not values:
                    return
                name = values[0].replace("📁 ", "").replace("📄 ", "")
                if not getattr(self, 'current_path', None):
                    return
                full_path = os.path.join(self.current_path, name)
                self.on_file_click(full_path)

    def _on_right_click(self, event):
        """Handle right-click - show context menu."""
        # Close any existing menu first
        self.context_menu.unpost()

        # Select item under cursor if not already selected
        item = self.tree.identify_row(event.y)
        if item and item not in self.tree.selection():
            self.tree.selection_set(item)
        if item:
            self.tree.focus(item)
            # Get item info
            values = self.tree.item(item, "values")
            if values:
                # Show context menu at cursor position
                try:
                    self.context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu.grab_release()
                    
    def _selection_is_single_file(self):
        """Return True if exactly one file is selected."""
        selected = self.tree.selection()
        if len(selected) != 1:
            return False
        path = self._resolve_single_path(selected[0])
        return path and os.path.isfile(path)

    def _resolve_single_path(self, iid):
        """Resolve one tree item ID to a path."""
        text = self.tree.item(iid, "text")
        if text and os.path.isabs(text):
            return text
        values = self.tree.item(iid, "values")
        if not values:
            return None
        name = values[0].replace("📁 ", "").replace("📄 ", "")
        if getattr(self, 'current_path', None):
            return os.path.join(self.current_path, name)
        return None

    def _on_context_open(self):
        """Context menu: Open."""
        if self.on_context_menu:
            selected = self.tree.selection()
            if len(selected) == 1:
                self.on_context_menu("open", self._get_selected_item_path())

    def _on_context_open_with(self):
        """Context menu: Open With."""
        if self.on_context_menu and self._selection_is_single_file():
            self.on_context_menu("open_with", self._get_selected_item_path())
            
    def _on_context_new_folder(self):
        """Context menu: New Folder."""
        if self.on_context_menu:
            self.on_context_menu("new_folder", self.current_path)

    def _on_context_new_file(self):
        """Context menu: New File."""
        if self.on_context_menu:
            self.on_context_menu("new_file", self.current_path)

    def _on_context_copy(self):
        """Context menu: Copy."""
        if self.on_context_menu:
            self.on_context_menu("copy", self._get_selected_item_path())

    def _on_context_paste(self):
        """Context menu: Paste."""
        if self.on_context_menu:
            self.on_context_menu("paste", self.current_path)
            
    def _on_context_rename(self):
        """Context menu: Rename (single selection only)."""
        selected = self.tree.selection()
        if self.on_context_menu and len(selected) == 1:
            self.on_context_menu("rename", self._get_selected_item_path())

    def _on_context_remove(self):
        """Context menu: Remove selected item(s)."""
        if self.on_context_menu:
            selected = self.tree.selection()
            if len(selected) > 1:
                self.on_context_menu("remove", None)
            else:
                self.on_context_menu("remove", self._get_selected_item_path())
            
    def _on_context_copy_path(self):
        """Context menu: Copy Path (single selection only)."""
        selected = self.tree.selection()
        if self.on_context_menu and len(selected) == 1:
            self.on_context_menu("copy_path", self._get_selected_item_path())

    def _on_context_properties(self):
        """Context menu: Properties (single selection only)."""
        selected = self.tree.selection()
        if self.on_context_menu and len(selected) == 1:
            self.on_context_menu("properties", self._get_selected_item_path())

    def _on_context_extract_archive(self):
        """Context menu: Extract selected archive to current directory."""
        selected = self.tree.selection()
        if self.on_context_menu and len(selected) == 1:
            self.on_context_menu("extract_archive", self._get_selected_item_path())

    def _on_context_create_archive(self):
        """Context menu: Create archive from selected items."""
        selected = self.tree.selection()
        if self.on_context_menu and selected:
            paths = self.get_selected_item_paths()
            if paths:
                self.on_context_menu("create_archive", paths)
            
    def get_selected_item_paths(self):
        """Get paths of all selected items (supporting multi-select)."""
        selected = self.tree.selection()
        if not selected:
            return []
        paths = []
        for iid in selected:
            text = self.tree.item(iid, "text")
            if text and os.path.isabs(text):
                paths.append(text)
                continue
            values = self.tree.item(iid, "values")
            if not values:
                continue
            name = values[0].replace("📁 ", "").replace("📄 ", "")
            if hasattr(self, 'current_path') and self.current_path:
                paths.append(os.path.join(self.current_path, name))
        return paths

    def _get_selected_item_path(self):
        """Get path of currently selected item.

        In recursive search mode the item's Treeview text holds the full path.
        """
        item = self.tree.selection()
        if not item:
            return None
        iid = item[0]
        # Recursive search stores absolute path in the Treeview text field
        text = self.tree.item(iid, "text")
        if text and os.path.isabs(text):
            return text
        values = self.tree.item(iid, "values")
        if not values:
            return None
        name = values[0].replace("📁 ", "").replace("📄 ", "")
        if hasattr(self, 'current_path') and self.current_path:
            return os.path.join(self.current_path, name)
        return None
        
    def set_current_path(self, path):
        """Set the current directory path."""
        self.current_path = path
        
    def _on_double_click(self, event):
        """Handle double-click event."""
        self.on_double_click(event)

    def _on_key_up(self, event=None):
        """Move selection up."""
        item = self.tree.focus()
        prev = self.tree.prev(item)
        if prev:
            if event and (event.state & 0x0001):  # Shift held
                self._shift_select_to(prev)
                self._track_anchor()
            else:
                self.tree.selection_set(prev)
                self.tree.focus(prev)
            self.tree.see(prev)
        return "break"

    def _track_anchor(self, event=None):
        """Update selection anchor for Shift selection."""
        sel = self.tree.selection()
        if sel:
            self._selection_anchor = sel[0]

    def _shift_select_to(self, item):
        """Extend selection from anchor to item."""
        anchor = self._selection_anchor or self.tree.focus()
        if not anchor:
            self.tree.selection_set(item)
            self.tree.focus(item)
            self._selection_anchor = item
            return
        all_items = self.tree.get_children("")
        try:
            idx1 = all_items.index(anchor)
            idx2 = all_items.index(item)
        except ValueError:
            self.tree.selection_set(item)
            self.tree.focus(item)
            return
        start, end = sorted((idx1, idx2))
        self.tree.selection_set(all_items[start:end + 1])
        self.tree.focus(item)

    def _on_key_down(self, event=None):
        """Move selection down."""
        item = self.tree.focus()
        next_item = self.tree.next(item)
        if next_item:
            if event and (event.state & 0x0001):  # Shift held
                self._shift_select_to(next_item)
                self._track_anchor()
            else:
                self.tree.selection_set(next_item)
                self.tree.focus(next_item)
            self.tree.see(next_item)
        return "break"

    def _on_key_return(self, event=None):
        """Open selected item(s) (only single selection)."""
        selected = self.tree.selection()
        if len(selected) == 1 and self.on_double_click:
            self.on_double_click(event)
        return "break"

    def _on_key_backspace(self, event=None):
        """Navigate to parent directory."""
        if self.on_context_menu:
            self.on_context_menu("go_to_parent", self.current_path)
        return "break"

    def _on_key_delete(self, event=None):
        """Delete selected item(s)."""
        selected = self.tree.selection()
        if selected and self.on_context_menu:
            if len(selected) > 1:
                self.on_context_menu("remove", None)
            else:
                self.on_context_menu("remove", self._get_selected_item_path())
        return "break"

    def _on_key_rename(self, event=None):
        """Rename selected item (single only)."""
        selected = self.tree.selection()
        if len(selected) == 1 and self.on_context_menu:
            self.on_context_menu("rename", self._get_selected_item_path())
        return "break"

    def clear(self):
        """Clear all items from the tree."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
    def insert_item(self, name, display_name, size, modified, file_type, thumbnail=None):
        """
        Insert an item into the file tree.

        Args:
            name: Internal name
            display_name: Display name with icon
            size: File size string
            modified: Modified date string
            file_type: File type description
            thumbnail: Optional tk.PhotoImage thumbnail for image files
        """
        if self._thumbnails_enabled and thumbnail is not None:
            # Show image in the icon column (#0) and keep full text in values[0]
            self.tree.insert(
                "", "end", text=name, image=thumbnail,
                values=(display_name, size, modified, file_type)
            )
        else:
            self.tree.insert("", "end", text=name, values=(display_name, size, modified, file_type))
        
    def get_selection(self):
        """Get currently selected item."""
        return self.tree.selection()
        
    def get_item_values(self, item):
        """Get values from item."""
        return self.tree.item(item, "values")
        
    def set_path(self, path):
        """Set the path in the path bar."""
        self.path_var.set(path)
        
    def bind_path_entry(self, callback):
        """Bind Enter key on path entry."""
        self.path_entry.bind("<Return>", callback)
        
    def bind_up_button(self, callback):
        """Bind Up button click."""
        self.up_btn.config(command=callback)
        
    def bind_refresh_button(self, callback):
        """Bind Refresh button click."""
        self.refresh_btn.config(command=callback)
        
    def add_to_paned_window(self, weight=1):
        """Add this panel to the parent PanedWindow."""
        self.parent.add(self.frame, weight=weight)
