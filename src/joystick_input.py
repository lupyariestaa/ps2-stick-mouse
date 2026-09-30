"""Wrapper pembacaan input stik (joystick) berbasis pygame.

Modul ini membungkus pygame.joystick agar modul lain cukup memanggil method
sederhana untuk mendapatkan posisi axis atau status tombol.
"""

from __future__ import annotations

import time

import pygame


class JoystickNotFoundError(RuntimeError):
    """Dilempar ketika stik tidak ditemukan."""


class JoystickReader:
    """Pembaca input stik dengan antarmuka sederhana."""

    def __init__(self, index: int = 0) -> None:
        pygame.init()
        pygame.joystick.init()

        count = pygame.joystick.get_count()
        if count == 0:
            raise JoystickNotFoundError(
                "Tidak ada stik yang terdeteksi. Pastikan adaptor PS2->USB "
                "sudah dicolok dan stik menyala."
            )
        if index >= count:
            raise JoystickNotFoundError(
                f"Stik index {index} tidak ada. Hanya {count} stik terdeteksi "
                f"(index valid: 0..{count - 1})."
            )

        self._index = index
        self._joy = pygame.joystick.Joystick(index)
        self._joy.init()

        self._num_axes = self._joy.get_numaxes()
        self._num_buttons = self._joy.get_numbuttons()
        self._num_hats = self._joy.get_numhats()

        # Buang event/state awal agar tidak false-trigger saat startup.
        # Stik sering mengirim nilai tombol/axis "sampah" di beberapa frame
        # pertama setelah inisialisasi.
        for _ in range(5):
            pygame.event.pump()
            time.sleep(0.01)

    # -- Properti informasi -------------------------------------------------

    @property
    def name(self) -> str:
        return self._joy.get_name()

    @property
    def num_axes(self) -> int:
        return self._num_axes

    @property
    def num_buttons(self) -> int:
        return self._num_buttons

    @property
    def num_hats(self) -> int:
        return self._num_hats

    @property
    def index(self) -> int:
        return self._index

    # -- Pembacaan input ----------------------------------------------------

    def pump(self) -> None:
        """Proses event pygame agar state input ter-update."""
        pygame.event.pump()

    def axis(self, axis_id: int, default: float = 0.0) -> float:
        """Ambil nilai sebuah axis (-1.0 .. 1.0)."""
        if axis_id < 0 or axis_id >= self._num_axes:
            return default
        return self._joy.get_axis(axis_id)

    def button(self, button_id: int, default: bool = False) -> bool:
        """Ambil status sebuah tombol (True = ditekan)."""
        if button_id < 0 or button_id >= self._num_buttons:
            return default
        return bool(self._joy.get_button(button_id))

    def hat(self, hat_id: int = 0) -> tuple[int, int]:
        """Ambil nilai hat/D-Pad (dx, dy)."""
        if hat_id < 0 or hat_id >= self._num_hats:
            return (0, 0)
        return self._joy.get_hat(hat_id)

    def close(self) -> None:
        """Bersihkan sumber daya pygame."""
        pygame.joystick.quit()
        pygame.quit()


def list_joysticks() -> list[dict]:
    """Kembalikan daftar stik yang terdeteksi beserta infonya (untuk T1.1)."""
    pygame.init()
    pygame.joystick.init()

    joysticks = []
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        joysticks.append(
            {
                "index": i,
                "name": joy.get_name(),
                "axes": joy.get_numaxes(),
                "buttons": joy.get_numbuttons(),
                "hats": joy.get_numhats(),
            }
        )
    return joysticks
