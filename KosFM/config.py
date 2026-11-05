"""
Configuration file for KosFM Application.
Contains constants, settings, and default values.
"""

from . import __version__ as _pkg_version

# Application Information
APP_NAME = "KosFM"
APP_VERSION = _pkg_version
AUTHOR = "KosFM Team"

# Window Settings
WINDOW_SIZE = "1200x700"
MIN_WINDOW_SIZE = (800, 500)

# Preview panel default height as fraction of screen height
PREVIEW_HEIGHT_RATIO = 0.50
PREVIEW_MIN_HEIGHT = 140
PREVIEW_MAX_HEIGHT = 700

# UI Settings
TREE_WIDTH = 300
PANEL_PADDING = 5

# Icons
FOLDER_ICON = "📁"
FILE_ICON = "📄"

# Tree View Settings
TREE_COLUMNS = ("name",)
FILE_COLUMNS = ("name", "size", "modified", "type")

# File Types for Icons (future use)
FILE_TYPE_FOLDER = "folder"
FILE_TYPE_FILE = "file"

# Default Starting Path
DEFAULT_PATH = "."  # Current directory

# Supported Image Extensions (for future preview feature)
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico')

# File size units
SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB']
