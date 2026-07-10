
"""
Dialog modules for KosFM.
Contains dialog windows for file operations.
"""

import os
import tkinter as tk
from tkinter import ttk
import platform
from pathlib import Path

from .utils.xdg_mime import (
    get_mime_type,
    get_default_application,
    set_default_application,
    find_applications_for_mime_type,
    launch_application,
    parse_desktop_file
)
from .utils.file_utils import format_size, format_time


class OpenWithDialog:
    """Open With dialog for choosing application to open files."""
    
    def __init__(self, parent, file_path, config_manager, config, status_callback):
        """
        Initialize Open With dialog.
        
        Args:
            parent: Parent window (root)
            file_path: Path to file to open
            config_manager: ConfigManager instance
            config: Current config dict
            status_callback: Function to call to update status bar
        """
        self.parent = parent
        self.file_path = file_path
        self.config_manager = config_manager
        self.config = config
        self.status_callback = status_callback
        
        self.dialog = None
        self.listbox = None
        self.app_index = {}
        self.set_default_var = None
        
    def show(self):
        """Show the dialog."""
        mime_type = get_mime_type(self.file_path)
        if not mime_type:
            self._show_error(f"Could not determine file type: {self.file_path}")
            return
            
        # Find all apps for this MIME type
        apps = find_applications_for_mime_type(mime_type)
        
        if not apps:
            self._show_error(f"No applications found for {mime_type}")
            return
            
        # Get current default
        default_app = get_default_application(mime_type)
        
        # Create dialog
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Open With - {os.path.basename(self.file_path)}")
        self.dialog.geometry("450x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Main container with padding
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text=f"File type: {mime_type}").pack(pady=(0, 10), anchor="w")
        
        # Create listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(pady=5, fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=12)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Populate listbox
        self.app_index = {}
        for i, app in enumerate(apps):
            display = app['name']
            if default_app and app['desktop_file'] == default_app:
                display += " (default)"
            self.listbox.insert("end", display)
            self.app_index[i] = app
            
        # Select first item
        if apps:
            self.listbox.select_set(0)
            
        # Set as default checkbox
        self.set_default_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Set as default for this file type", 
                       variable=self.set_default_var).pack(pady=10, anchor="w")
        
        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(10, 0), fill="x")
        
        # Center the button
        btn_frame.columnconfigure(0, weight=1)
        open_btn = ttk.Button(btn_frame, text="Open", command=self._do_open, width=15)
        open_btn.grid(row=0, column=0)
        
    def _do_open(self):
        """Handle Open button click."""
        selection = self.listbox.curselection()
        if not selection:
            return
        app = self.app_index.get(selection[0])
        if app:
            mime_type = get_mime_type(self.file_path)
            
            # Save preference if checkbox is checked
            if self.set_default_var.get():
                set_default_application(mime_type, app['desktop_file'])
                # Also save in our config
                if "mime_apps" not in self.config:
                    self.config["mime_apps"] = {}
                self.config["mime_apps"][mime_type] = app['desktop_file']
                self.config_manager.save_config(self.config)
            
            # Launch the file
            launch_application(self.file_path, app)
            self.status_callback(f"Opening with {app['name']}: {self.file_path}")
        self.dialog.destroy()
        
    def _show_error(self, message):
        """Show error message."""
        from tkinter import messagebox
        print(f"Error: {message}")
        messagebox.showerror("Error", message)


class PropertiesDialog:
    """File properties dialog."""
    
    def __init__(self, parent, file_path):
        """
        Initialize Properties dialog.
        
        Args:
            parent: Parent window (root)
            file_path: Path to file to show properties for
        """
        self.parent = parent
        self.file_path = file_path
        
    def show(self):
        """Show the dialog."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Properties")
        dialog.geometry("400x300")
        dialog.transient(self.parent)
        
        try:
            stat = os.stat(self.file_path)
            
            info = {
                "Name": os.path.basename(self.file_path),
                "Path": self.file_path,
                "Type": "Folder" if os.path.isdir(self.file_path) else "File",
                "Size": format_size(stat.st_size) if os.path.isfile(self.file_path) else "N/A",
                "Created": format_time(stat.st_ctime),
                "Modified": format_time(stat.st_mtime),
                "Accessed": format_time(stat.st_atime),
            }
            
            if platform.system() != "Windows":
                info["Permissions"] = oct(stat.st_mode)[-3:]
                
        except OSError as e:
            info = {"Error": str(e)}
            
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill="both", expand=True)
        
        row = 0
        for key, value in info.items():
            ttk.Label(frame, text=f"{key}:", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Label(frame, text=str(value), wraplength=250).grid(row=row, column=1, sticky="w", padx=10, pady=2)
            row += 1
            
        ttk.Button(dialog, text="OK", command=dialog.destroy).pack(pady=10)
