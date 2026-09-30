"""Mengetik teks hasil STT dan menekan Enter (via pynput)."""

from __future__ import annotations

import time

from pynput.keyboard import Controller, Key


class TextTyper:
    """Mengetik teks ke aplikasi yang sedang fokus."""

    def __init__(self, interval: float = 0.01) -> None:
        self._kb = Controller()
        self.interval = interval

    def type_text(self, text: str) -> None:
        """Ketik teks karakter demi karakter."""
        if not text:
            return
        for ch in text:
            try:
                self._kb.type(ch)
            except Exception:
                # Beberapa karakter khusus mungkin gagal; lewati.
                pass
            if self.interval > 0:
                time.sleep(self.interval)

    def press_enter(self) -> None:
        """Tekan tombol Enter."""
        self._kb.press(Key.enter)
        self._kb.release(Key.enter)
