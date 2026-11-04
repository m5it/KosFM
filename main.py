#!/usr/bin/env python3
"""
KosFM - Entry point
A simple file manager with tree view and file listing.
"""

import os
import sys
import tkinter as tk

# Add project-local venv site-packages if it exists (for optional Pillow)
_VENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "lib")
if os.path.isdir(_VENV):
    for lib_dir in os.listdir(_VENV):
        site_pkg = os.path.join(_VENV, lib_dir, "site-packages")
        if os.path.isdir(site_pkg) and site_pkg not in sys.path:
            sys.path.insert(0, site_pkg)

from KosFM.app import KosFMApp
from KosFM.config import APP_NAME


def main():
    """Application entry point."""
    try:
        root = tk.Tk()
        root.title(APP_NAME)
        app = KosFMApp(root)
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}", file=sys.stderr)
        sys.exit(1)



if __name__ == "__main__":
    main()
