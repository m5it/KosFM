
"""
File opener utility for KosFM.
Handles cross-platform file opening with default applications.
"""

import os
import platform
import subprocess


def open_file_default(path):
    """
    Open file with default system application.
    
    Args:
        path: Full path to file
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.isfile(path):
        return False
        
    system = platform.system()
    
    try:
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", path], check=True)
        else:  # Linux and others
            subprocess.run(["xdg-open", path], check=True)
        return True
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Error opening file: {e}")
        return False


def open_file_with(path, command):
    """
    Open file with specific application.
    
    Args:
        path: Full path to file
        command: Application command (e.g., "gimp", "firefox")
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.isfile(path):
        return False
        
    try:
        subprocess.Popen([command, path], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        return True
    except (OSError, FileNotFoundError) as e:
        print(f"Error opening file with {command}: {e}")
        return False


def get_file_mime_type(path):
    """
    Get MIME type of file (if available).
    
    Args:
        path: Full path to file
        
    Returns:
        str: MIME type or None
    """
    try:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(path)
        return mime_type
    except ImportError:
        return None
