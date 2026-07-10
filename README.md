
# KosFM

A simple, cross-platform file manager built with Python and tkinter. Features a dual-pane interface with a resizable directory tree on the left and file listing on the right. Now with Linux desktop integration via xdg-mime!

![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey.svg)

## Features

- **Dual-Pane Interface**: Resizable directory tree on the left, file listing on the right
- **Linux Desktop Integration**: Full xdg-mime support for file associations
- **File Operations**: Copy, Paste, Rename, and Remove files/directories
- **Context Menu**: Right-click menu with Open, Open With, Copy, Paste, Rename, Remove, Copy Path, Properties
- **Panel Width Persistence**: Panel sizes are saved and restored between sessions
- **File Opening**: Double-click to open files with default application
- **Open With**: Choose from available applications and set defaults
- **Application Detection**: Automatically finds all apps that can handle a file type
- **Saved Preferences**: Remembers your "Open With" choices between sessions
- **Lazy Loading**: Directories load on-demand for better performance
- **File Details**: View file size, modification date, and type
- **Resizable Panels**: Drag the divider to adjust panel widths
- **Navigation**: 
  - Click directories in tree to view contents
  - Double-click folders to navigate into them
  - "Up" button to go to parent directory
  - Path bar for direct navigation
- **Menu Bar**: File, View, and Help menus with keyboard shortcuts
- **View Options**: Toggle hidden files and status bar visibility
- **Window State**: Saves position, size, and panel widths between sessions
- **Icons**: Visual distinction with emoji icons (📁 folders, 📄 files)
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Error Handling**: Graceful handling of permission errors and inaccessible directories
- **Status Bar**: Shows item count and current path

## Screenshots

```
┌─────────────────────────────────────────────────────────┐
│ File  View  Help                           [KosFM]    │
├──────────────────┬────────────────────────────────────┤
│ 📁 Directory     │ ⬆ Up  [/home/user/projects]  🔄    │
│ ├── 📁 home      ├────────────────────────────────────┤
│ ├── 📁 root      │ 📁 src        │      │2024-01-15│   │
│ │   └── 📁 user  │ 📄 main.py    │ 15KB │2024-01-15│   │
│       └── 📁 proj│ 📄 config.py  │  811B│2024-01-15│   │
│           ├── 📁 │ 📄 README.md  │ 2.5KB│2024-01-15│   │
│           └── 📄 │                                   │   │
│                  │ 4 items (2 folders, 2 files)      │   │
└──────────────────┴────────────────────────────────────┘
```

## File Operations

KosFM now includes full file operation support:

- **Copy** - Copy file/directory to clipboard
- **Paste** - Paste into current directory (auto-handles duplicates with suffix)
- **Rename** - Rename files and directories with dialog
- **Remove** - Delete files and directories with confirmation

All operations include proper error handling and user confirmation for destructive actions.

## File Opening (Linux)

KosFM integrates with your Linux desktop environment using `xdg-mime`:

- **Double-click** any file to open with its default application
- **Right-click** → "Open With..." to choose from available applications
- **Set as default** checkbox to make an app the default for that file type
- **Saved preferences** persist between sessions in `config.json`

Supported features:
- MIME type detection via `xdg-mime query filetype`
- Application discovery from `/usr/share/applications` and `~/.local/share/applications`
- .desktop file parsing (Name, Icon, Exec, MimeType)
- Field code handling (%f, %F, %u, %U in Exec lines)
- System-wide default setting via `xdg-mime default`

## Project Structure

```
KosFM/
├── main.py                 # Entry point
├── install.py              # Installation script
├── KosFM/                  # Main package
│   ├── __init__.py
│   ├── config.py           # Constants and settings
│   ├── app.py              # Main application controller
│   ├── dialogs.py          # Dialog handlers (Open With, Properties)
│   ├── navigation.py       # Navigation logic
│   ├── ui/                 # UI components
│   │   ├── __init__.py
│   │   ├── tree_panel.py   # Directory tree widget
│   │   ├── file_panel.py   # File listing widget
│   │   ├── menu_bar.py     # Menu bar
│   │   └── status_bar.py   # Status bar
│   └── utils/              # Utility modules
│       ├── __init__.py
│       ├── config_manager.py # Config save/load
│       ├── error_handler.py  # Error handling
│       ├── file_utils.py     # File formatting
│       ├── platform_utils.py # Platform-specific code
│       └── xdg_mime.py       # Linux MIME type handling
├── README.md               # This file
└── CHANGELOG.md            # Version history
```

## Requirements

- Python 3.6 or higher
- tkinter (included with Python standard library)

## Installation

1. Clone or download this repository
2. Run the installer:
   ```bash
   ./install.py --install
   ```
3. Or run directly:
   ```bash
   python main.py
   ```

## Usage

Run the file manager:

```bash
kosfm
# or
python main.py
```

### Navigation

| Action | Description |
|--------|-------------|
| Click folder in tree | View contents in right panel |
| Double-click folder | Navigate into folder |
| Double-click file | Open file with default application |
| Click "Up" button | Go to parent directory |
| Type path + Enter | Navigate to specific path |
| Click "Refresh" | Reload current directory |
| Drag divider | Resize left/right panels (size is saved) |

### Context Menu (Right-Click)

| Option | Description |
|--------|-------------|
| Open | Open file with default application |
| Open With... | Choose application to open file |
| Copy | Copy file/directory to clipboard |
| Paste | Paste from clipboard to current directory |
| Rename | Rename file or directory |
| Remove | Delete file or directory (with confirmation) |
| Copy Path | Copy full path to clipboard |
| Properties | Show file details |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+R | Refresh current directory |
| Ctrl+Q | Exit application |

## Menu Bar

### File Menu
| Option | Shortcut | Description |
|--------|----------|-------------|
| Refresh | Ctrl+R | Reload current directory |
| Exit | Ctrl+Q | Close application |

### View Menu
| Option | Description |
|--------|-------------|
| Show Hidden Files | Toggle visibility of hidden files (.*) |
| Show Status Bar | Toggle status bar at bottom |

### Help Menu
| Option | Description |
|--------|-------------|
| Keyboard Shortcuts | Show all available shortcuts |
| About | Application information |

## Configuration

Configuration is automatically saved to `~/.config/KosFM/config.json` and includes:
- Window position and size
- Panel divider position (saved automatically when resized)
- View options (show hidden files, show status bar)
- MIME type application preferences (saved "Open With" choices)

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Linux | ✅ Supported | Full xdg-mime integration, file operations |
| Windows | ✅ Supported | Shows all drives (C:\, D:\, etc.) |
| macOS | ✅ Supported | Shows / and /Users |

## Modular Architecture

The application is organized into focused modules:

- **main.py**: Minimal entry point
- **KosFM/app.py**: Main application controller
- **KosFM/dialogs.py**: Dialog handlers (Open With, Properties)
- **KosFM/navigation.py**: Navigation logic
- **KosFM/ui/**: Self-contained UI widgets
- **KosFM/utils/**: Reusable utility functions
- **KosFM/config.py**: Centralized constants

This structure makes the code easy to maintain, test, and extend.

## Future Enhancements

- [ ] File preview panel
- [ ] Search functionality
- [ ] Bookmarks/favorites
- [ ] Dark theme
- [ ] Additional keyboard shortcuts
- [ ] File type icons (replace emoji with actual icons)
- [ ] Drag and drop support
- [ ] Archive handling (zip, tar, etc.)
- [ ] Image thumbnails

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available under the MIT License.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

**Current Version: 1.4.0** - Now with file operations (Copy, Paste, Rename, Remove) and panel width persistence!
