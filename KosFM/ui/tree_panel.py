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
    
    def __init__(self, parent, on_select_callback, on_expand_callback):
        """
        Initialize tree panel.
        
        Args:
            parent: Parent widget (PanedWindow)
            on_select_callback: Function to call when item selected
            on_expand_callback: Function to call when item expanded
        """
        self.parent = parent
        self.on_select = on_select_callback
        self.on_expand = on_expand_callback
        
        self._create_widget()
        
    def _create_widget(self):
        """Create the tree panel widget."""
        # Create frame for tree panel
        self.frame = ttk.Frame(self.parent, padding=(0, 0, PANEL_PADDING, 0))
        
        # Create Treeview for directory tree
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
        
    def add_to_paned_window(self, weight=0):
        """Add this panel to the parent PanedWindow."""
        self.parent.add(self.frame, weight=weight)
