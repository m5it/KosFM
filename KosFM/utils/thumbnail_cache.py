"""
Optional thumbnail generation for KosFM.
Requires Pillow; degrades gracefully when not installed.
"""

import os
import threading
import tkinter as tk
from pathlib import Path


THUMBNAIL_SIZE = (32, 32)
_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', '.tiff')

_PILLOW_AVAILABLE = None
_ImageModule = None

def _ensure_pillow():
    global _PILLOW_AVAILABLE, _ImageModule
    if _PILLOW_AVAILABLE is not None:
        return _PILLOW_AVAILABLE
    try:
        from PIL import Image as _Image
        _ImageModule = _Image
        _PILLOW_AVAILABLE = True
        return True
    except ImportError:
        _PILLOW_AVAILABLE = False
        return False


def pillow_available():
    """Return True if Pillow is installed."""
    return _ensure_pillow()


def is_image_file(path):
    """Return True if the path has a known image extension."""
    if not path:
        return False
    return path.lower().endswith(_IMAGE_EXTENSIONS)


class ThumbnailCache:
    """Cache of tk.PhotoImage thumbnails, optionally generated via Pillow."""

    def __init__(self, size=THUMBNAIL_SIZE):
        self.size = size
        self._cache = {}
        self._lock = threading.Lock()
        self._placeholder = None

    def get_thumbnail(self, path):
        """Return a tk.PhotoImage for the image path, or None if unavailable."""
        if not path or not os.path.isfile(path):
            return None
        if not is_image_file(path):
            return None
        if not pillow_available():
            return None

        with self._lock:
            if path in self._cache:
                return self._cache[path]

        try:
            photo = self._generate(path)
        except Exception:
            photo = None

        if photo is None:
            return None

        with self._lock:
            # In case another thread already cached it, prefer existing
            if path in self._cache:
                return self._cache[path]
            self._cache[path] = photo
        return photo

    def _generate(self, path):
        """Generate a thumbnail PhotoImage using Pillow."""
        if _ImageModule is None:
            return None
        try:
            from PIL import ImageTk
            img = _ImageModule.open(path)
            if img.mode not in ("RGB", "RGBA", "L"):
                try:
                    img = img.convert("RGBA")
                except Exception:
                    img = img.convert("RGB")
            img.thumbnail(self.size)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def clear(self):
        """Clear cached thumbnails."""
        with self._lock:
            self._cache.clear()

    def forget(self, path):
        """Remove a specific path from cache."""
        with self._lock:
            self._cache.pop(path, None)
