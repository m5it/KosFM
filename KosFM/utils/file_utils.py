"""
File utility functions for KosFM.
"""

from datetime import datetime

from ..config import SIZE_UNITS


def format_size(size):
    """Format file size in human-readable format."""
    for unit in SIZE_UNITS:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_time(timestamp):
    """Format timestamp for display."""
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M")


def get_file_type(entry):
    """Get file type description."""
    if entry.is_dir():
        return "Folder"
    else:
        name = entry.name
        if '.' in name:
            ext = name.rsplit('.', 1)[-1].upper()
            return f"{ext} File"
        return "File"
