"""Auto-boost volume mikrofon (berdasarkan temuan FASE V0).

Volume mikrofon di laptop ini awalnya sangat pelan (~3%), membuat STT gagal.
Modul ini menaikkan volume device input ke 100% & memastikannya tidak mute.
"""

from __future__ import annotations

import warnings
from ctypes import cast, POINTER

# Redam UserWarning dari pycaw untuk device yang tidak mendukung kontrol volume
# (device output/tidak aktif). Warning ini tidak berbahaya.
warnings.filterwarnings("ignore", message=".*COMError.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pycaw")

try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    _HAS_PYCAW = True
except ImportError:  # pragma: no cover - opsional
    _HAS_PYCAW = False


def boost_microphone_volume(target: float = 1.0) -> int:
    """Naikkan volume semua device audio ke `target` (0.0-1.0) & unmute.

    Kembalikan jumlah device yang berhasil diproses.
    """
    if not _HAS_PYCAW:
        return 0

    count = 0
    try:
        devices = AudioUtilities.GetAllDevices()
    except Exception:
        return 0

    for dev in devices:
        try:
            interface = dev._dev.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None
            )
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(target, None)
            volume.SetMute(0, None)
            count += 1
        except Exception:
            # Device output / tidak mendukung -> abaikan.
            pass
    return count
