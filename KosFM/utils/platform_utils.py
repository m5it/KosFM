"""
Platform-specific utilities for KosFM.
"""

import os
import platform
import string


def get_root_directories():
    """
    Get root directories based on platform.
    
    Returns:
        list: List of tuples (path, display_name) for root directories.
    """
    system = platform.system()
    
    if system == "Windows":
        return _get_windows_drives()
    else:
        return _get_unix_roots()


def _get_windows_drives():
    """Get Windows drive letters."""
    from ctypes import windll
    
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drive_path = f"{letter}:\\"
            drives.append((drive_path, drive_path))
        bitmask >>= 1
    return drives


def _get_unix_roots():
    """Get Unix root directories."""
    roots = [("/", "/")]
    home = os.path.expanduser("~")
    home_name = os.path.basename(home) or "home"
    roots.append((home, home_name))
    return roots
