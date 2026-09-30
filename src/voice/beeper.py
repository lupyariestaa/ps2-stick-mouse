"""Feedback suara sederhana (bip) via winsound (Windows)."""

from __future__ import annotations

import threading

try:
    import winsound

    _HAS_WINSOUND = True
except ImportError:  # non-Windows
    _HAS_WINSOUND = False


def _beep(freq: int, duration: int) -> None:
    if _HAS_WINSOUND:
        try:
            winsound.Beep(freq, duration)
        except Exception:
            pass


def _beep_async(freq: int, duration: int) -> None:
    """Jalankan beep di thread agar tidak memblokir main loop."""
    threading.Thread(target=_beep, args=(freq, duration), daemon=True).start()


def beep_start() -> None:
    """Bip tanda mulai merekam (nada tinggi)."""
    _beep_async(880, 120)


def beep_stop() -> None:
    """Bip tanda berhenti merekam (nada rendah)."""
    _beep_async(440, 120)


def beep_error() -> None:
    """Bip tanda error."""
    _beep_async(300, 250)
