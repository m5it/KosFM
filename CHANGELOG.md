# Changelog

All notable changes to the KosFM project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-07-09

### Added
- **Modular Architecture**: Complete refactor from monolithic structure to organized modules
  - New package structure: `KosFM/` with `ui/` and `utils/` subpackages
  - Separated concerns: UI components, utilities, and main application
  - Each module is focused and maintainable (30-300 lines)
- **Resizable Panels**: Draggable divider between tree and file panels using `ttk.PanedWindow`
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

### v1.2.0 (2026-07-09)
- 🏗️ **Major refactor**: Modular architecture
- ✨ Resizable panels with draggable divider
- ✨ Window state persistence (position, size, panel widths)
- 📁 New project structure with organized packages

### v1.1.0 (2026-07-09)
- ✨ Added menu bar with File, View, and Help menus
- ✨ Added Show/Hide Hidden Files option
- ✨ Added Status Bar toggle
- ✨ Added Keyboard Shortcuts and About dialogs

### v1.0.0 (2026-07-09)
- 🎉 First stable release
- Complete file manager with tree view and file listing
- Basic navigation and error handling
- Cross-platform compatibility

### v0.1.0 (Development)
- Project initialization
- Basic window setup
- Initial tree view implementation
