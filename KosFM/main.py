#!/usr/bin/env python3
"""
KosFM - Entry point
A simple file manager with tree view and file listing.
"""

import sys
import tkinter as tk

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
