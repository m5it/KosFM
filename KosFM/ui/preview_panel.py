
"""
Preview panel widget for KosFM.
Shows a quick preview of the currently selected file or directory.
"""

import os
import tkinter as tk
from tkinter import ttk

from ..utils.file_utils import format_size, format_time, get_file_type
from ..utils.thumbnail_cache import is_image_file, pillow_available


class PreviewPanel:
    """Preview panel that displays info and a snippet of selected items."""

    TEXT_PREVIEW_BYTES = 8 * 1024
    TEXT_MAX_LINES = 40

    def __init__(self, parent):
        """Initialize preview panel."""
        self.parent = parent
        self._thumbnail_cache = None
        self._current_image = None
        self._create_widget()

    def _create_widget(self):
        """Create the preview panel widgets."""
        self.frame = ttk.Frame(self.parent, padding="5")
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)

        self.title_var = tk.StringVar(value="Preview")
        self.title_label = ttk.Label(self.frame, textvariable=self.title_var,
                                     font=("TkDefaultFont", 10, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        # Info row with resize checkbox on the right
        self.info_frame = ttk.Frame(self.frame)
        self.info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        self.info_frame.columnconfigure(0, weight=1)
        self.info_frame.columnconfigure(1, weight=0)

        self.info_var = tk.StringVar(value="")
        self.info_label = ttk.Label(self.info_frame, textvariable=self.info_var,
                                    wraplength=300, justify="left")
        self.info_label.grid(row=0, column=0, sticky="nw")

        self.fit_preview_var = tk.BooleanVar(value=True)
        self._fit_mode = True
        self.fit_preview_check = ttk.Checkbutton(
            self.info_frame,
            text="Fit to panel",
            variable=self.fit_preview_var,
            command=self._on_fit_toggle
        )
        self.fit_preview_check.grid(row=0, column=1, sticky="ne", padx=(6, 0))

        # Canvas for image preview so it can fill and re-center dynamically
        self.image_canvas = tk.Canvas(self.frame, highlightthickness=0)
        self.image_canvas.grid(row=2, column=0, sticky="nsew", pady=(0, 4))
        self.image_canvas.grid_remove()
        self.frame.rowconfigure(2, minsize=120, weight=1)

        # Make image area resizable with mouse wheel when focused
        self.frame.bind("<Control-MouseWheel>", self._on_wheel_zoom)
        self.frame.bind("<Control-Button-4>", self._on_wheel_zoom)
        self.frame.bind("<Control-Button-5>", self._on_wheel_zoom)

        self.content_text = tk.Text(self.frame, wrap="word", state="disabled",
                                    height=6, padx=4, pady=4)
        self.content_text.grid(row=3, column=0, sticky="nsew")
        self.frame.rowconfigure(3, weight=1)

        self.v_scrollbar = ttk.Scrollbar(self.frame, orient="vertical",
                                          command=self.content_text.yview)
        self.v_scrollbar.grid(row=3, column=1, sticky="ns")
        self.content_text.configure(yscrollcommand=self.v_scrollbar.set)

        # Track parent and frame size to recalculate fit
        self._last_image_path = None
        self._fit_mode = True
        self.parent.bind("<Configure>", self._on_parent_configure)
        self.frame.bind("<Configure>", self._on_parent_configure)

    def clear(self):
        """Clear the preview panel."""
        self.title_var.set("Preview")
        self.info_var.set("No selection")
        self._last_image_path = None
        self._hide_image()
        self._set_content("")

    def show_path(self, path):
        """Show preview for the given filesystem path."""
        if not path or not os.path.exists(path):
            self.clear()
            return

        name = os.path.basename(path)
        try:
            stat = os.stat(path)
            size = format_size(stat.st_size)
            modified = format_time(stat.st_mtime)
        except OSError:
            size = "?"
            modified = "?"

        if os.path.isdir(path):
            self.title_var.set(f"📁 {name}")
            try:
                count = len(os.listdir(path))
            except OSError:
                count = "?"
            self.info_var.set(f"Directory\n{count} items\n{modified}")
            self._hide_image()
            self._set_content("")
            return

        # File
        file_type = get_file_type(type('E', (), {'is_dir': lambda s, **kw: False, 'name': name})())
        self.title_var.set(f"📄 {name}")
        self.info_var.set(f"{file_type}\n{size}\n{modified}")

        if is_image_file(path):
            self._last_image_path = path
            # Try Pillow-based scaled preview first, then tk fallback, then thumbnail cache
            if not pillow_available():
                if self._show_image_tk_fallback(path):
                    return
                # No tk fallback either
                self._hide_image()
                ext = os.path.splitext(path)[1].upper().lstrip(".") or "Image"
                self._set_content(f"{ext} image — install Pillow for better preview\n{path}\n{size}")
                return
            if self._show_image(path):
                return
            if self._thumbnail_cache is None:
                from ..utils.thumbnail_cache import ThumbnailCache
                self._thumbnail_cache = ThumbnailCache(size=(200, 200))
            cached = self._thumbnail_cache.get_thumbnail(path)
            if cached:
                self._current_image = cached
                self._place_image(cached)
                self.image_canvas.grid()
                self.content_text.grid_remove()
                self.v_scrollbar.grid_remove()
                return
            # Fallback when no preview possible
            self._hide_image()
            ext = os.path.splitext(path)[1].upper().lstrip(".") or "Image"
            if pillow_available():
                self._set_content(f"{ext} image — thumbnail failed")
            else:
                self._set_content(f"{ext} image — install Pillow for better preview\n{path}\n{size}")
            return

        self._hide_image()
        text = self._read_text_preview(path)
        if text is not None:
            lines = text.splitlines()
            if len(lines) > self.TEXT_MAX_LINES:
                text = "\n".join(lines[:self.TEXT_MAX_LINES]) + "\n…"
            self._set_content(text)
        else:
            self._set_content("[Binary file — no text preview]")

    def _show_image(self, path):
        """Try to show an image preview; return True on success."""
        if self._thumbnail_cache is None:
            from ..utils.thumbnail_cache import ThumbnailCache
            self._thumbnail_cache = ThumbnailCache(size=(200, 200))
        # Ensure canvas is visible before measuring
        self.image_canvas.grid()
        self.content_text.grid_remove()
        self.v_scrollbar.grid_remove()
        self.frame.update_idletasks()
        # Load scaled image directly
        photo = self._load_scaled_image(path)
        if photo is None:
            photo = self._thumbnail_cache.get_thumbnail(path)
        if photo is None:
            return False
        self._current_image = photo
        self._place_image(photo)
        return True

    def _place_image(self, photo):
        """Center image on canvas and keep a reference."""
        self.image_canvas.delete("all")
        self.image_canvas.image = photo  # keep reference
        w, h = photo.width(), photo.height()
        cw = max(w, self.image_canvas.winfo_width())
        ch = max(h, self.image_canvas.winfo_height())
        x = (cw - w) // 2
        y = (ch - h) // 2
        self.image_canvas.create_image(x, y, anchor="nw", image=photo)

    def _load_scaled_image(self, path):
        """Load image scaled to fit within current preview frame (Pillow only)."""
        if not pillow_available():
            return None
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            # Convert palette/CMYK safely
            if img.mode not in ("RGB", "RGBA", "L"):
                try:
                    img = img.convert("RGBA")
                except Exception:
                    img = img.convert("RGB")
            if self._fit_mode:
                # Use canvas's allocated size when mapped
                cw = self.image_canvas.winfo_width()
                ch = self.image_canvas.winfo_height()
                # If not mapped yet, fall back to frame size
                if cw < 10 or ch < 10:
                    cw = self.frame.winfo_width() - 10
                    ch = self.frame.winfo_height() - 80
                max_w = max(64, cw - 4)
                max_h = max(64, ch - 4)
            else:
                # "Actual size" mode but still capped to avoid huge preview
                max_w = max(64, min(800, img.width))
                max_h = max(64, min(800, img.height))
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _on_fit_toggle(self):
        """Handle Fit checkbox toggle."""
        self._fit_mode = self.fit_preview_var.get()
        if self._last_image_path:
            self.show_path(self._last_image_path)

    def _on_parent_configure(self, event=None):
        """Re-scale current image when preview panel or top-level window is resized."""
        if not self._last_image_path or not self._current_image:
            return
        if not self._fit_mode:
            return  # only auto-resize in fit mode
        # Debounce: schedule resize after user stops dragging
        if hasattr(self, '_resize_after_id'):
            try:
                self.frame.after_cancel(self._resize_after_id)
            except Exception:
                pass

        def _do_resize():
            try:
                self.frame.update_idletasks()
                self.parent.update_idletasks()
                new_w = max(64, self.image_canvas.winfo_width() - 4)
                new_h = max(64, self.image_canvas.winfo_height() - 4)
                old_w = self._current_image.width()
                old_h = self._current_image.height()
                # If canvas has room to grow or shrink significantly, reload
                if new_w > old_w or new_h > old_h or new_w < old_w * 0.8 or new_h < old_h * 0.8:
                    self._show_image(self._last_image_path)
            except Exception:
                pass

        # Wait for PanedWindow to finish geometry propagation
        self._resize_after_id = self.frame.after(700, _do_resize)

    def _force_preview_resize(self):
        """Immediately update the image to fill the available preview space."""
        if not self._last_image_path or not self._current_image:
            return
        if not self._fit_mode:
            return
        try:
            self.frame.update_idletasks()
            self.parent.update_idletasks()
            self._show_image(self._last_image_path)
        except Exception:
            pass

    def _hide_image(self):
        """Hide image preview and restore text widget."""
        self._current_image = None
        self.image_canvas.delete("all")
        self.image_canvas.grid_remove()
        self.content_text.grid()
        self.v_scrollbar.grid()

    def _read_text_preview(self, path):
        """Try to read a text preview of the file. Returns None if binary."""
        try:
            with open(path, "rb") as f:
                chunk = f.read(self.TEXT_PREVIEW_BYTES)
            if b"\x00" in chunk:
                return None
            encodings = ("utf-8", "latin-1", "cp1252")
            for enc in encodings:
                try:
                    return chunk.decode(enc)
                except UnicodeDecodeError:
                    continue
            return None
        except (OSError, PermissionError):
            return None

    def _set_content(self, text):
        """Set the content text widget text."""
        self.content_text.configure(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", text)
        self.content_text.configure(state="disabled")

    def _on_wheel_zoom(self, event=None):
        """Zoom image preview with Ctrl+mouse wheel (Linux wheel events)."""
        if not self._last_image_path or not self._fit_mode:
            return
        delta = 0
        if event is None:
            return
        if hasattr(event, 'delta'):
            delta = event.delta
        elif event.num == 4:
            delta = 120
        elif event.num == 5:
            delta = -120
        if delta == 0:
            return
        # Resize preview pane: positive = bigger preview, negative = smaller
        parent = self.parent
        try:
            total = parent.winfo_height()
            current = total - parent.sashpos(0)
            step = int(total * 0.05)
            new_preview = max(80, min(total - 100, current + (step if delta > 0 else -step)))
            parent.sashpos(0, total - new_preview)
        except Exception:
            pass

    def set_theme_colors(self, bg, fg):
        """Apply theme colors to the text widget."""
        try:
            self.content_text.configure(bg=bg, fg=fg,
                                          insertbackground=fg,
                                          selectbackground=fg,
                                          selectforeground=bg)
        except Exception:
            pass

    def _show_image_tk_fallback(self, path):
        """Show image via tk.PhotoImage when Pillow is unavailable (PNG/GIF)."""
        try:
            if not path.lower().endswith((".png", ".gif")):
                return False
            photo = tk.PhotoImage(file=path)
            self._current_image = photo
            self.image_canvas.grid()
            self._place_image(photo)
            self.content_text.grid_remove()
            self.v_scrollbar.grid_remove()
            return True
        except Exception:
            return False
