
"""
File panel widget for KosFM.
Displays file listing with details.
"""

import os
import tkinter as tk
from tkinter import ttk

from ..config import FILE_COLUMNS, PANEL_PADDING
from ..utils.file_opener import open_file_default


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
        
        self._create_widget()
        self._create_context_menu()
        
    def _create_widget(self):
        """Create the file panel widget."""
        # Create frame for file panel
        self.frame = ttk.Frame(self.parent)
        
        # Configure grid
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        
        # Create path bar
        self._create_path_bar()
        
        # Create file tree
        self._create_file_tree()
        
    def _create_path_bar(self):
        """Create the path bar."""
        self.path_frame = ttk.Frame(self.frame)
        self.path_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
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
        """Create the file listing tree."""
        tree_frame = ttk.Frame(self.frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=FILE_COLUMNS,
            selectmode="browse",
            show="headings"
        )
        
        # Configure columns
        self.tree.heading("name", text="Name", anchor="w")
        self.tree.heading("size", text="Size", anchor="e")
        self.tree.heading("modified", text="Modified", anchor="w")
        self.tree.heading("type", text="Type", anchor="w")
        
        self.tree.column("name", width=300, minwidth=150, stretch=True)
        self.tree.column("size", width=80, minwidth=60, stretch=False)
        self.tree.column("modified", width=150, minwidth=100, stretch=False)
        self.tree.column("type", width=80, minwidth=60, stretch=False)
        
        # Scrollbars
        self.v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Bind events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-1>", self._on_single_click)
        self.tree.bind("<Button-3>", self._on_right_click)  # Right-click
        self.tree.bind("<Control-Button-1>", self._on_right_click)  # Ctrl+click (macOS)
        
    def _create_context_menu(self):
        """Create right-click context menu."""
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Open", command=self._on_context_open)
        self.context_menu.add_command(label="Open With...", command=self._on_context_open_with)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy", command=self._on_context_copy)
        self.context_menu.add_command(label="Paste", command=self._on_context_paste)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Rename", command=self._on_context_rename)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Remove", command=self._on_context_remove)
        self.context_menu.add_separator()

    def _on_single_click(self, event):
        """Handle single click - just select item, don't open."""
        # Close context menu if open
        self.context_menu.unpost()
        
        item = self.tree.identify_row(event.y)
        if not item:
            return
            
        # Select the item
        self.tree.selection_set(item)
        
        # Call the file click callback if set (for custom handling)
        if self.on_file_click:
            values = self.tree.item(item, "values")
            if values:
                name = values[0].replace("📁 ", "").replace("📄 ", "")
                if hasattr(self, 'current_path') and self.current_path:
                    full_path = os.path.join(self.current_path, name)
                    self.on_file_click(full_path)
            full_path = os.path.join(self.current_path, name)
            if os.path.isfile(full_path):
                # It's a file - open it
                if self.on_file_click:
                    self.on_file_click(full_path)
                else:
                    # Default behavior: open with system default
                    open_file_default(full_path)
                    
    def _on_right_click(self, event):
        """Handle right-click - show context menu."""
        # Close any existing menu first
        self.context_menu.unpost()
        
        # Select item under cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            # Get item info
            values = self.tree.item(item, "values")
            if values:
                # Show context menu at cursor position
                try:
                    self.context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu.grab_release()
                    
    def _on_context_open(self):
        """Context menu: Open."""
        if self.on_context_menu:
            self.on_context_menu("open", self._get_selected_item_path())
            
    def _on_context_open_with(self):
        """Context menu: Open With."""
        if self.on_context_menu:
            self.on_context_menu("open_with", self._get_selected_item_path())
            
    def _on_context_copy(self):
        """Context menu: Copy."""
        if self.on_context_menu:
            self.on_context_menu("copy", self._get_selected_item_path())
            
    def _on_context_paste(self):
        """Context menu: Paste."""
        if self.on_context_menu:
            self.on_context_menu("paste", self.current_path)
            
    def _on_context_rename(self):
        """Context menu: Rename."""
        if self.on_context_menu:
            self.on_context_menu("rename", self._get_selected_item_path())
            
    def _on_context_remove(self):
        """Context menu: Remove."""
        if self.on_context_menu:
            self.on_context_menu("remove", self._get_selected_item_path())
            
    def _on_context_copy_path(self):
        """Context menu: Copy Path."""
        if self.on_context_menu:
            self.on_context_menu("copy_path", self._get_selected_item_path())
            
    def _on_context_properties(self):
        """Context menu: Properties."""
        if self.on_context_menu:
            self.on_context_menu("properties", self._get_selected_item_path())
            
    def _get_selected_item_path(self):
        """Get path of currently selected item."""
        item = self.tree.selection()
        if not item:
            return None
        values = self.tree.item(item[0], "values")
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
        
    def clear(self):
        """Clear all items from the tree."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
    def insert_item(self, name, display_name, size, modified, file_type):
        """
        Insert an item into the file tree.
        
        Args:
            name: Internal name
            display_name: Display name with icon
            size: File size string
            modified: Modified date string
            file_type: File type description
        """
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
