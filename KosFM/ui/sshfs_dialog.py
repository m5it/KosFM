"""
Dialog for connecting to SSHFS remote hosts.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


class SSHFSConnectDialog(simpledialog.Dialog):
    """Dialog to enter SSHFS connection details."""

    def __init__(self, parent, title="Connect to SSHFS", initial=None):
        self.result_data = None
        self.initial = initial or {}
        super().__init__(parent, title=title)

    def body(self, master):
        """Create dialog body."""
        ttk.Label(master, text="User@Host:/path").grid(row=0, column=0, sticky="w", pady=2)
        self.host_var = tk.StringVar(value=self.initial.get("host", "user@example.com:/home/user"))
        self.host_entry = ttk.Entry(master, textvariable=self.host_var, width=40)
        self.host_entry.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(master, text="Alias (optional)").grid(row=1, column=0, sticky="w", pady=2)
        self.alias_var = tk.StringVar(value=self.initial.get("alias", ""))
        ttk.Entry(master, textvariable=self.alias_var, width=40).grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(master, text="Port").grid(row=2, column=0, sticky="w", pady=2)
        self.port_var = tk.StringVar(value=self.initial.get("port", "22"))
        ttk.Entry(master, textvariable=self.port_var, width=10).grid(row=2, column=1, sticky="w", pady=2)

        self.use_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(master, text="Use SSH key", variable=self.use_key_var,
                        command=self._toggle_key).grid(row=3, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Label(master, text="Identity file").grid(row=4, column=0, sticky="w", pady=2)
        self.key_var = tk.StringVar(value=self.initial.get("identity_file", os.path.expanduser("~/.ssh/id_rsa")))
        self.key_entry = ttk.Entry(master, textvariable=self.key_var, width=40, state="disabled")
        self.key_entry.grid(row=4, column=1, sticky="ew", pady=2)

        self.use_password_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(master, text="Use password (requires sshpass)", variable=self.use_password_var,
                        command=self._toggle_password).grid(row=5, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Label(master, text="Password").grid(row=6, column=0, sticky="w", pady=2)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(master, textvariable=self.password_var, show="*", width=40, state="disabled")
        self.password_entry.grid(row=6, column=1, sticky="ew", pady=2)

        return self.host_entry

    def _toggle_key(self):
        state = "normal" if self.use_key_var.get() else "disabled"
        self.key_entry.configure(state=state)

    def _toggle_password(self):
        state = "normal" if self.use_password_var.get() else "disabled"
        self.password_entry.configure(state=state)

    def validate(self):
        """Validate input."""
        host = self.host_var.get().strip()
        if not host:
            messagebox.showwarning("Invalid input", "Please enter a host.")
            return False
        if ":" not in host:
            messagebox.showwarning("Invalid input", "Host must include a path, e.g. user@host:/path")
            return False
        port = self.port_var.get().strip()
        if port and not port.isdigit():
            messagebox.showwarning("Invalid input", "Port must be a number.")
            return False
        return True

    def apply(self):
        """Return connection data."""
        self.result_data = {
            "host": self.host_var.get().strip(),
            "alias": self.alias_var.get().strip() or None,
            "port": int(self.port_var.get().strip()) if self.port_var.get().strip() else None,
            "identity_file": self.key_var.get().strip() if self.use_key_var.get() else None,
            "password": self.password_var.get() if self.use_password_var.get() else None,
        }

    def show(self):
        """Return result data (Dialog.__init__ already blocks)."""
        return self.result_data


class SSHFSDisconnectDialog(simpledialog.Dialog):
    """Dialog to pick an active SSHFS mount to disconnect."""

    def __init__(self, parent, aliases, title="Disconnect SSHFS"):
        self.aliases = aliases
        self.selected = None
        super().__init__(parent, title=title)

    def body(self, master):
        ttk.Label(master, text="Select mount to disconnect:").pack(pady=4)
        self.listbox = tk.Listbox(master, height=6)
        self.listbox.pack(fill="both", expand=True, padx=4, pady=4)
        for alias in self.aliases:
            self.listbox.insert("end", alias)
        if self.aliases:
            self.listbox.select_set(0)
        return self.listbox

    def apply(self):
        sel = self.listbox.curselection()
        if sel:
            self.selected = self.aliases[sel[0]]

    def show(self):
        return self.selected
