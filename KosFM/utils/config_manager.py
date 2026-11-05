"""
Configuration manager for KosFM.
Handles save/load of window state and user preferences.
"""

import copy
import json
from pathlib import Path

from ..config import TREE_WIDTH


class ConfigManager:
    """Manages application configuration and window state."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "KosFM"
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            "window": {
                "width": 1200,
                "height": 700,
                "x": 100,
                "y": 100
            },
            "panel": {
                "left_width": TREE_WIDTH,
                "right_top_height": 70,
                "preview_height": 120
            },
            "view": {
                "show_hidden_files": False,
                "show_status_bar": True,
                "show_preview_panel": True
            },
            "mime_apps": {},
            "bookmarks": [],
            "sort": {
                "column": "name",
                "reverse": False
            },
            "theme": "light",
            "thumbnails": {
                "enabled": True
            },
            "sshfs_mounts": {},
            "sshfs_last": {
                "host": "user@example.com:/home/user",
                "alias": "",
                "port": "22",
                "identity_file": "~/.ssh/id_rsa"
            },
            "last_path": "~"
        }
        
    def ensure_config_dir(self):
        """Create config directory if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(self):
        """Load configuration from JSON file."""
        self.ensure_config_dir()
        
        if not self.config_file.exists():
            return self.default_config.copy()
            
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Deep merge with defaults to ensure all keys exist
                merged = copy.deepcopy(self.default_config)
                for key, value in config.items():
                    if isinstance(value, dict) and isinstance(merged.get(key), dict):
                        merged[key].update(value)
                    else:
                        merged[key] = value
                return merged
        except (json.JSONDecodeError, IOError):
            return copy.deepcopy(self.default_config)
            
    def save_config(self, config):
        """Save configuration to JSON file."""
        self.ensure_config_dir()
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")
