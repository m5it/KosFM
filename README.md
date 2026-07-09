# File Manager

A simple, cross-platform file manager built with Python and tkinter. Features a dual-pane interface with a directory tree on the left and file listing on the right.

![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Dual-Pane Interface**: Directory tree on the left, file listing on the right
- **Lazy Loading**: Directories load on-demand for better performance
- **File Details**: View file size, modification date, and type
- **Navigation**: 
  - Click directories in tree to view contents
  - Double-click folders to navigate into them
  - "Up" button to go to parent directory
  - Path bar for direct navigation
- **Icons**: Visual distinction with emoji icons (📁 folders, 📄 files)
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Error Handling**: Graceful handling of permission errors and inaccessible directories
- **Status Bar**: Shows item count and current path

## Screenshots

```
┌─────────────────────────────────────────────────────────┐
│  File Manager                              [Window]   │
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

## Requirements

- Python 3.6 or higher
- tkinter (included with Python standard library)

## Installation

1. Clone or download this repository
2. No additional dependencies required!

## Usage

Run the file manager:

```bash
python main.py
```

### Navigation

| Action | Description |
|--------|-------------|
| Click folder in tree | View contents in right panel |
| Double-click folder | Navigate into folder |
| Click "Up" button | Go to parent directory |
| Type path + Enter | Navigate to specific path |
| Click "Refresh" | Reload current directory |

## Project Structure

```
file-manager/
├── main.py           # Main application file
├── config.py         # Configuration constants
├── requirements.txt  # Dependencies (empty - uses stdlib)
├── assets/           # Future: icons and resources
├── README.md         # This file
└── CHANGELOG.md      # Version history
```

## Configuration

Edit `config.py` to customize:

- `WINDOW_SIZE` - Default window size (default: "1200x700")
- `TREE_WIDTH` - Width of left panel (default: 300)
- `DEFAULT_PATH` - Starting directory (default: current directory)
- `FOLDER_ICON` / `FILE_ICON` - Change icons

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Windows | ✅ Supported | Shows all drives (C:\, D:\, etc.) |
| macOS | ✅ Supported | Shows / and /Users |
| Linux | ✅ Supported | Shows / and /home |

## Keyboard Shortcuts

- `Enter` (in path bar) - Navigate to entered path
- `F5` - Refresh (future feature)

## Error Handling

The application handles common errors gracefully:

- **Permission Denied**: Shows "Access Denied" message
- **File Not Found**: Error dialog with details
- **System Errors**: User-friendly error messages

## Future Enhancements

- [ ] File operations (copy, move, delete, rename)
- [ ] Context menu (right-click)
- [ ] File preview panel
- [ ] Search functionality
- [ ] Bookmarks/favorites
- [ ] Dark theme
- [ ] Keyboard shortcuts
- [ ] File type icons (different icons for different file types)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available under the MIT License.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
