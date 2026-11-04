"""
File utility functions for KosFM.
"""

import os
from datetime import datetime

from ..config import SIZE_UNITS


def is_archive(path):
    """Check whether a path is a supported archive file."""
    from .archive_handler import ARCHIVE_EXTENSIONS
    if not os.path.isfile(path):
        return False
    name_lower = path.lower()
    return any(name_lower.endswith(ext) for ext in ARCHIVE_EXTENSIONS)


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
        if is_archive(entry.path if hasattr(entry, 'path') else name):
            return "Archive"
        if '.' in name:
            ext = name.rsplit('.', 1)[-1].upper()
            return f"{ext} File"
        return "File"
