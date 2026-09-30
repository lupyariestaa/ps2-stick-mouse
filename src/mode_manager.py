"""Pengelola mode: MOUSE atau GAMEPAD.

Pada FASE 1, program berjalan di MOUSE mode. Toggle tombol sudah disiapkan
agar FASE 2 bisa mengaktifkannya dengan mudah.
"""

from __future__ import annotations

from enum import Enum


class Mode(Enum):
    MOUSE = "MOUSE"
    GAMEPAD = "GAMEPAD"


class ModeManager:
    """Menyimpan mode aktif dan menangani logika toggle."""

    def __init__(self, initial: Mode = Mode.MOUSE) -> None:
        self._mode = initial
        self._toggle_was_down = False

    @property
    def mode(self) -> Mode:
        return self._mode

    @property
    def is_mouse(self) -> bool:
        return self._mode is Mode.MOUSE

    def set_mode(self, mode: Mode) -> bool:
        """Set mode. Kembalikan True bila mode benar-benar berubah."""
        if mode is self._mode:
            return False
        self._mode = mode
        return True

    def toggle(self) -> Mode:
        """Balik mode MOUSE <-> GAMEPAD."""
        self._mode = Mode.GAMEPAD if self.is_mouse else Mode.MOUSE
        return self._mode

    def update_toggle(self, button_down: bool) -> bool:
        """Deteksi penekanan tombol toggle (edge-triggered).

        Kembalikan True TEPAT saat tombol berpindah dari lepas -> ditekan.
        """
        triggered = button_down and not self._toggle_was_down
        self._toggle_was_down = button_down
        return triggered
