"""
Tree panel widget for KosFM.
Displays the directory tree with lazy loading.
"""

import os
import tkinter as tk
from tkinter import ttk

from ..config import TREE_WIDTH, PANEL_PADDING, FOLDER_ICON


class TreePanel:
    """Directory tree panel widget."""
    
    def __init__(self, parent, on_select_callback, on_expand_callback,
                 on_bookmark_select=None):
        """
        Initialize tree panel.

        Args:
            parent: Parent widget (PanedWindow)
            on_select_callback: Function to call when directory item selected
            on_expand_callback: Function to call when item expanded
            on_bookmark_select: Function to call when bookmark selected
        """
        self.parent = parent
        self._select_callback = on_select_callback
        self._expand_callback = on_expand_callback
        self._bookmark_callback = on_bookmark_select
        self._bookmarks = {}

        self._create_widget()

    @property
    def on_select(self):
        return self._select_callback

    @on_select.setter
    def on_select(self, callback):
        self._select_callback = callback

    @property
    def on_expand(self):
        return self._expand_callback

    @on_expand.setter
    def on_expand(self, callback):
        self._expand_callback = callback

    @property
    def on_bookmark_select(self):
        return self._bookmark_callback

    @on_bookmark_select.setter
    def on_bookmark_select(self, callback):
        self._bookmark_callback = callback

    def set_theme_colors(self, bg, fg):
        """Apply theme colors to internal non-ttk widgets if needed."""
        pass  # Treeview handled via ttk style; placeholder for future widgets

    def _create_widget(self):
        """Create the tree panel widget."""
        # Create frame for tree panel
        self.frame = ttk.Frame(self.parent, padding=(0, 0, PANEL_PADDING, 0))

        # Create Treeview for directory tree + bookmarks
        self.tree = ttk.Treeview(
            self.frame,
            columns=("name",),
            selectmode="browse",
            show="tree"
        )
        self.tree.heading("#0", text="Directory", anchor="w")
        self.tree.column("#0", width=TREE_WIDTH, minwidth=150, stretch=True)

        # Add scrollbar for tree
        self.scrollbar = ttk.Scrollbar(
            self.frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Grid tree and scrollbar
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure frame grid
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        # Bind events
        self.tree.bind("<<TreeviewOpen>>", self._on_expand)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        # Fallback for environments where <<TreeviewSelect>> doesn't fire reliably
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)
        self.tree.bind("<Button-3>", self._on_tree_right_click)
        self.tree.bind("<Delete>", self._on_bookmark_delete)
        self._last_handled_iid = None

    def set_select_callback(self, callback):
        """Set callback for directory selection."""
        self._select_callback = callback

    def set_bookmark_callback(self, callback):
        """Set callback for bookmark selection."""
        self._bookmark_callback = callback

    def _on_tree_right_click(self, event):
        """Right-click on tree - select item but don't show native menu yet."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            # No default menu; bookmarks handled via app if needed

    def _on_bookmark_delete(self, event=None):
        """Delete key on a bookmark node signals remove request to app."""
        item = self.tree.focus()
        if not item:
            return
        if item in self._bookmarks:
            path = self._bookmarks[item]
            self.tree.delete(item)
            del self._bookmarks[item]
            if self.on_bookmark_select:
                self.on_bookmark_select("remove", path)
        
    def _on_expand(self, event):
        """Handle tree node expansion."""
        item = self.tree.focus()
        if not item:
            return
        path = self.tree.item(item, "values")[0] if self.tree.item(item, "values") else ""
        if not path:
            return
        children = self.tree.get_children(item)
        if children and self.tree.item(children[0], "text") == "dummy":
            self.tree.delete(children[0])
            self.on_expand(item, path)
            
    def _on_select(self, event):
        """Handle tree selection."""
        sel = self.tree.selection()
        if sel:
            self._last_handled_iid = sel[0]
        self.on_select(event)

    def _on_tree_click(self, event):
        """Handle mouse click on a tree row as a fallback navigation trigger."""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        # If TreeviewSelect already handled this row, skip to avoid double navigation
        if item == self._last_handled_iid:
            self._last_handled_iid = None
            return
        # Update selection to the clicked row and notify app
        self.tree.selection_set(item)
        self.tree.focus(item)
        self._last_handled_iid = item
        self.on_select(event)
        
    def insert_node(self, parent, path, text, has_children=False):
        """
        Insert a node into the tree.
        
        Args:
            parent: Parent item ID or empty string for root
            path: Full path for the node
            text: Display text
            has_children: Whether to show expand arrow
            
        Returns:
            Node ID
        """
        display_text = f"{FOLDER_ICON} {text}"
        node_id = self.tree.insert(parent, "end", text=display_text, values=(path,), open=False)
        
        if has_children:
            self.tree.insert(node_id, "end", text="dummy", values=("",))
            
        return node_id
        
    def get_selection(self):
        """Get currently selected item."""
        return self.tree.selection()
        
    def get_item_path(self, item):
        """Get path from item."""
        return self.tree.item(item, "values")[0] if self.tree.item(item, "values") else ""
        
    def add_bookmark_node(self, path, label):
        """Add a bookmark entry under the Bookmarks section."""
        section = self._ensure_bookmarks_section()
        display_text = f"⭐ {label}"
        node_id = self.tree.insert(section, "end", text=display_text, values=(path,))
        self._bookmarks[node_id] = path
        return node_id

    def remove_bookmark_node(self, path):
        """Remove bookmark node by path."""
        for node_id, node_path in list(self._bookmarks.items()):
            if node_path == path:
                self.tree.delete(node_id)
                del self._bookmarks[node_id]

    def clear_bookmarks(self):
        """Remove all bookmark nodes."""
        section = self._bookmarks_section()
        if section:
            self.tree.delete(section)
        self._bookmarks.clear()

    def _ensure_bookmarks_section(self):
        """Return the Bookmarks section node, creating it if needed."""
        section = self._bookmarks_section()
        if section:
            return section
        return self.tree.insert("", 0, text="⭐ Bookmarks", values=("",), open=True)

    def _bookmarks_section(self):
        """Return existing Bookmarks section node or None."""
        for child in self.tree.get_children(""):
            text = self.tree.item(child, "text")
            if text.startswith("⭐ Bookmarks"):
                return child
        return None

    def is_bookmark_node(self, item):
        """Check whether an item ID is a bookmark node."""
        return item in self._bookmarks

    def add_to_paned_window(self, weight=0):
        """Add this panel to the parent PanedWindow."""
        self.parent.add(self.frame, weight=weight)
