
# Changelog

All notable changes to KosFM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-07-09

### Added
- **Linux xdg-mime Integration**: Full support for Linux desktop file associations
  - MIME type detection via `xdg-mime query filetype`
  - Automatic discovery of applications from .desktop files
  - Single-click file opening with default application
  - "Open With" dialog showing all apps for a file type
  - "Set as default" checkbox to save preferences
  - Saved preferences persist in config.json
  - System-wide default setting via `xdg-mime default`
- **Right-Click Context Menu**: New context menu on files with options:
  - **Open**: Open file with default application
  - **Open With...**: Choose from available applications
  - **Copy Path**: Copy file path to clipboard
  - **Properties**: Show file details dialog
- **New Utils Module**: `xdg_mime.py` with functions:
  - `get_mime_type()` - Detect MIME type
  - `get_default_application()` - Get default app
  - `set_default_application()` - Set system default
  - `find_applications_for_mime_type()` - Find all compatible apps
  - `parse_desktop_file()` - Parse .desktop files
  - `launch_application()` - Launch with specific app
  - `open_file_with_default()` - Open via xdg-open

### Changed
- **File Opening**: Now uses xdg-mime on Linux for proper file associations
- **Config**: Added `mime_apps` section for saved application preferences
- **App**: Updated `_on_file_click()` to check saved preferences before opening

### Technical
- Scans `/usr/share/applications`, `/usr/local/share/applications`, and `~/.local/share/applications`
- Handles .desktop field codes (%f, %F, %u, %U)
- Supports wildcard MIME type matching (e.g., `image/*` matches `image/png`)
- Filters out NoDisplay and Hidden apps

## [1.2.0] - 2026-07-09

### Added
- **Window State Persistence**: Saves and restores:
  - Window position (x, y)
  - Window size (width, height)
  - Panel divider position
  - View options (hidden files, status bar visibility)
  - Stored in `~/.config/KosFM/config.json`

### Changed
- **Project Structure**: Complete reorganization
  - `main.py`: Now a minimal 27-line entry point
  - `KosFM/app.py`: Main application controller
  - `KosFM/ui/`: Tree panel, file panel, menu bar, status bar widgets
  - `KosFM/utils/`: Config manager, error handler, file utils, platform utils
- Improved code organization and maintainability
- Better separation of concerns

### Technical Details
- Uses relative imports within the package
- ConfigManager handles JSON config in ~/.config/KosFM/
- Each UI component is self-contained with clear interfaces
- Platform utilities abstract OS-specific code

## [1.1.0] - 2026-07-09

### Added
- **Menu Bar** with three menus:
  - **File Menu**: Refresh (Ctrl+R), Exit (Ctrl+Q)
  - **View Menu**: 
    - Show/Hide Hidden Files toggle
    - Show/Hide Status Bar toggle
  - **Help Menu**: Keyboard Shortcuts dialog, About dialog
- Hidden files filtering (files starting with `.`)
- Status bar visibility toggle
- Keyboard shortcuts for menu actions

## [1.0.0] - 2026-07-09

### Added
- Initial release of KosFM
- Dual-pane interface with directory tree and file listing
- Left panel: Directory tree with lazy loading
  - Platform-aware root directories (Windows drives / Unix root)
  - Expandable folders with on-demand loading
  - Folder icons (📁) for visual distinction
- Right panel: File listing with details
  - Columns: Name, Size, Modified Date, Type
  - Sorts folders first, then alphabetically
  - File icons (📄) for visual distinction
- Navigation features
  - Click tree items to view directory contents
  - Double-click folders to navigate into them
  - "Up" button for parent directory navigation
  - Path bar for direct path entry
  - Refresh button to reload current directory
- Status bar showing item count and current path
- Error handling for permission denied and system errors
- Cross-platform support (Windows, macOS, Linux)
- Human-readable file sizes (B, KB, MB, GB, TB)
- Formatted timestamps (YYYY-MM-DD HH:MM)

### Technical Details
- Built with Python 3.6+ and tkinter
- Uses `os.scandir()` for efficient directory scanning
- Implements `@handle_error` decorator for consistent error handling
- Lazy loading prevents freezing on large directories
- Configurable via `config.py`

## [Unreleased]

### Planned Features
- File operations (copy, move, delete, rename)
- Context menu on right-click
- File preview panel for images and text
- Search functionality across directories
- Bookmarks and favorites
- Dark theme support
- Additional keyboard shortcuts (F5 refresh, Ctrl+C copy, etc.)
- Different icons for different file types
- Drag and drop support
- Multi-select for batch operations

---

## Version History

### v1.3.0 (2026-07-09)
- ✨ **Linux xdg-mime Integration**: Full desktop file association support
- ✨ **File Opening**: Single-click opens files with correct application
- ✨ **Open With Dialog**: Choose from all available applications
- ✨ **Saved Preferences**: Remember "Open With" choices per MIME type
- 📋 New `xdg_mime.py` utility module
- 🐧 Linux-optimized file handling

### v1.2.0 (2026-07-09)
- ✨ **Modular Architecture**: Reorganized into focused modules
- ✨ **Resizable Panels**: PanedWindow for adjustable tree/file panels
- ✨ **Config Manager**: Persistent settings with JSON storage
- ✨ **Error Handler**: Decorator for graceful error handling
- 📋 Separated UI components (tree_panel, file_panel, menu_bar, status_bar)
- 📋 Utility modules (config_manager, error_handler, file_utils, platform_utils)

### v1.1.0 (2026-07-09)
- ✨ **Menu Bar**: File, View, and Help menus
- ✨ **Keyboard Shortcuts**: Ctrl+R (refresh), Ctrl+Q (exit)
- ✨ **View Options**: Toggle hidden files and status bar
- ✨ **Window State**: Save/restore position, size, and panel widths
- 📋 Help dialogs for shortcuts and about

### v1.0.0 (2026-07-09)
- ✨ **Initial Release**: Basic file manager functionality
- ✨ **Dual-Pane Layout**: Directory tree + file listing
- ✨ **Lazy Loading**: Directories load on demand
- ✨ **File Details**: Size, modification date, type
- ✨ **Navigation**: Tree click, double-click, Up button, path bar
- ✨ **Status Bar**: Item count and current path
- 📋 Cross-platform support (Windows, macOS, Linux)
