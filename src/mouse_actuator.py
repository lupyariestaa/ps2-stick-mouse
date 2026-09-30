"""Wrapper aksi mouse berbasis pynput.

Menyediakan API sederhana untuk menggerakkan kursor, klik, scroll, dan
melepas semua tombol (dipakai saat ganti mode / stik hilang).
"""

from __future__ import annotations

from pynput.mouse import Button, Controller


class MouseActuator:
    """Pengendali mouse."""

    def __init__(self) -> None:
        self._mouse = Controller()
        self._pressed: set[Button] = set()

    # -- Pergerakan ---------------------------------------------------------

    def move(self, dx: int, dy: int) -> None:
        """Geser kursor secara relatif terhadap posisi sekarang."""
        if dx == 0 and dy == 0:
            return
        self._mouse.move(dx, dy)

    # -- Klik ---------------------------------------------------------------

    def press(self, button: Button) -> None:
        """Tekan tombol mouse (tahan)."""
        if button in self._pressed:
            return
        self._mouse.press(button)
        self._pressed.add(button)

    def release(self, button: Button) -> None:
        """Lepas tombol mouse."""
        if button not in self._pressed:
            return
        self._mouse.release(button)
        self._pressed.discard(button)

    def click(self, button: Button) -> None:
        """Klik singkat (tekan lalu lepas)."""
        self._mouse.click(button, 1)

    def release_all(self) -> None:
        """Lepas semua tombol yang sedang ditekan (safety)."""
        for button in list(self._pressed):
            self._mouse.release(button)
        self._pressed.clear()

    # -- Scroll -------------------------------------------------------------

    def scroll(self, dx: int, dy: int) -> None:
        """Scroll roda mouse (dx horizontal, dy vertikal)."""
        if dx == 0 and dy == 0:
            return
        self._mouse.scroll(dx, dy)

    @property
    def position(self) -> tuple[int, int]:
        return self._mouse.position
