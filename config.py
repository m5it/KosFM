"""
Configuration file for File Manager Application.
Contains constants, settings, and default values.
"""

# Application Information
APP_NAME = "File Manager"
APP_VERSION = "1.0.0"
AUTHOR = "Developer"

# Window Settings
WINDOW_SIZE = "1200x700"
MIN_WINDOW_SIZE = (800, 500)

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