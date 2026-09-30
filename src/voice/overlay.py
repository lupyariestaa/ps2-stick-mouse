"""Overlay ikon mikrofon (tkinter) yang muncul di dekat kursor.

Overlay berjalan di thread terpisah dengan mainloop tkinter sendiri. Komunikasi
dari main loop dilakukan lewat method show()/hide() yang aman dari thread lain
(menggunakan `after` pada event loop tkinter).
"""

from __future__ import annotations

import os
import threading

try:
    import tkinter as tk

    _HAS_TK = True
except ImportError:  # pragma: no cover
    _HAS_TK = False


class MicOverlay:
    """Jendela kecil transparan menampilkan ikon mic di dekat kursor."""

    def __init__(self, icon_path: str | None = None, size: int = 72) -> None:
        self._icon_path = icon_path
        self._size = size
        self._root = None
        self._label = None
        self._image = None
        self._thread: threading.Thread | None = None
        self._enabled = _HAS_TK
        self._visible = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start(self) -> None:
        """Mulai thread overlay (mainloop tkinter)."""
        if not self._enabled:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            self._root = tk.Tk()
            self._root.overrideredirect(True)      # tanpa border/title bar
            self._root.attributes("-topmost", True)  # selalu di atas
            try:
                self._root.attributes("-alpha", 0.92)  # transparan
            except Exception:
                pass
            self._root.withdraw()  # sembunyi dulu

            # Muat gambar
            self._image = self._load_image()
            self._label = tk.Label(self._root, image=self._image, bg="white", borderwidth=1,
                                   relief="solid")
            self._label.pack()

            self._root.mainloop()
        except Exception:
            pass

    def _load_image(self):
        """Muat ikon dari file (PNG) atau buat default."""
        from .icon import create_mic_icon, ensure_mic_icon
        from PIL import ImageTk

        path = self._icon_path or ensure_mic_icon()
        if not os.path.exists(path):
            path = ensure_mic_icon()
        from PIL import Image

        img = Image.open(path).resize((self._size, self._size))
        return ImageTk.PhotoImage(img)

    # -- Kontrol (dipanggil dari main loop) --------------------------------

    def show(self, pos: tuple[int, int] | None = None) -> None:
        """Tampilkan overlay, opsional di posisi tertentu (dekat kursor)."""
        if not self._enabled or self._root is None:
            return
        try:
            self._root.after(0, lambda: self._show_impl(pos))
        except Exception:
            pass

    def _show_impl(self, pos) -> None:
        if pos is not None:
            x, y = pos
            self._root.geometry(f"+{x + 20}+{y + 20}")
        self._root.deiconify()
        self._root.attributes("-topmost", True)
        self._visible = True

    def hide(self) -> None:
        """Sembunyikan overlay."""
        if not self._enabled or self._root is None:
            return
        try:
            self._root.after(0, self._hide_impl)
        except Exception:
            pass

    def _hide_impl(self) -> None:
        self._root.withdraw()
        self._visible = False

    def stop(self) -> None:
        if self._root is not None:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass
            self._root = None
