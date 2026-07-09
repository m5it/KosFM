"""
Error handling utilities for KosFM.
"""

import traceback
from tkinter import messagebox


def handle_error(func):
    """Decorator for error handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PermissionError as e:
            args[0]._show_error(f"Permission denied: {e}")
        except FileNotFoundError as e:
            args[0]._show_error(f"File not found: {e}")
        except OSError as e:
            args[0]._show_error(f"System error: {e}")
        except Exception as e:
            args[0]._show_error(f"Unexpected error: {e}")
            traceback.print_exc()
    return wrapper
