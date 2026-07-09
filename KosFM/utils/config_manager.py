"""
Configuration manager for KosFM.
Handles save/load of window state and user preferences.
"""

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
                "left_width": TREE_WIDTH
            },
            "view": {
                "show_hidden_files": False,
                "show_status_bar": True
            }
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
                # Merge with defaults to ensure all keys exist
                merged = self.default_config.copy()
                merged.update(config)
                return merged
        except (json.JSONDecodeError, IOError):
            return self.default_config.copy()
            
    def save_config(self, config):
        """Save configuration to JSON file."""
        self.ensure_config_dir()
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")
