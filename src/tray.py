"""System tray icon (T3.4).

Menampilkan ikon di system tray dengan menu untuk:
- Menampilkan info status
- Ganti mode (Mouse/Gamepad)
- Keluar program

Tray berjalan di thread terpisah sehingga tidak mengganggu main loop.
Bila pystray/Pillow tidak tersedia, modul ini gagal secara aman (disabled).
"""

from __future__ import annotations

import threading
from typing import Callable

try:
    import pystray
    from PIL import Image, ImageDraw

    _HAS_TRAY = True
except ImportError:  # pragma: no cover - opsional
    _HAS_TRAY = False


def _make_icon_image(color: tuple[int, int, int] = (60, 130, 220)) -> "Image.Image":
    """Buat ikon sederhana (lingkaran) tanpa file gambar eksternal."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((6, 6, size - 6, size - 6), fill=color)
    # "kursor" kecil di tengah
    draw.polygon(
        [(size // 2, 20), (size // 2, 46), (size // 2 - 8, 38), (size // 2 + 8, 38)],
        fill=(255, 255, 255),
    )
    return img


class TrayIcon:
    """Wrapper tray icon yang aman (tidak crash bila library tidak ada)."""

    def __init__(
        self,
        on_quit: Callable[[], None],
        on_toggle_mode: Callable[[], None],
        get_status: Callable[[], str],
    ) -> None:
        self._on_quit = on_quit
        self._on_toggle_mode = on_toggle_mode
        self._get_status = get_status
        self._icon = None
        self._thread: threading.Thread | None = None
        self._enabled = _HAS_TRAY

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _build(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem(
                lambda item: self._get_status(), None, enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Ganti Mode (Mouse/Gamepad)", self._toggle),
            pystray.MenuItem("Keluar", self._quit),
        )
        self._icon = pystray.Icon(
            "stick_mouse",
            icon=_make_icon_image(),
            title="Stick PS2 -> Mouse",
            menu=menu,
        )

    def _toggle(self, icon=None, item=None) -> None:
        try:
            self._on_toggle_mode()
        except Exception:
            pass

    def _quit(self, icon=None, item=None) -> None:
        try:
            self._on_quit()
        finally:
            if self._icon is not None:
                self._icon.stop()

    def start(self) -> None:
        if not self._enabled:
            return
        self._build()
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def update(self) -> None:
        """Minta tray menyegarkan tooltip (status)."""
        if self._icon is not None:
            try:
                self._icon.update_menu()
            except Exception:
                pass

    def stop(self) -> None:
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
