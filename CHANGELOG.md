# Changelog

All notable changes to the File Manager project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Added
- Initial release of File Manager application
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
- Keyboard shortcuts (F5 refresh, Ctrl+C copy, etc.)
- Different icons for different file types
- Drag and drop support
- Multi-select for batch operations

---

## Version History

### v1.0.0 (2024-01-15)
- 🎉 First stable release
- Complete file manager with tree view and file listing
- Basic navigation and error handling
- Cross-platform compatibility

### v0.1.0 (Development)
- Project initialization
- Basic window setup
- Initial tree view implementation
