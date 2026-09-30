"""Loader & validasi konfigurasi untuk stick-mouse.

Modul ini bertanggung jawab membaca `config.json`, mengisi nilai default bila
ada field yang hilang, dan memvalidasi tipe/nilai dasar agar program tidak crash
karena config yang salah.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any


def _app_dir() -> str:
    """Direktori aplikasi (mendukung mode normal & PyInstaller .exe)."""
    if getattr(sys, "frozen", False):
        # Mode .exe: config disimpan di sebelah executable.
        return os.path.dirname(sys.executable)
    # Mode normal: root proyek (satu level di atas folder src/).
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Nilai default
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    "joystick_index": 0,
    "deadzone": 0.15,
    "startup_grace_seconds": 2.0,  # abaikan tombol selama N detik pertama
    "sensitivity": 12.0,
    "scroll_sensitivity": 1.0,
    "poll_interval_ms": 8,
    "invert_y": False,
    "smoothing": 0.0,            # 0.0 = tanpa smoothing, makin besar makin halus

    # --- Sensitivitas kursor (bisa diubah runtime lewat L1/R1) ---
    "sensitivity_step": 1.0,     # besar perubahan tiap tekan L1/R1
    "sensitivity_min": 2.0,      # batas bawah
    "sensitivity_max": 40.0,     # batas atas

    # --- Control buttons (WAJIB diverifikasi via src/diagnose.py) ---
    # Catatan: index tombol bergantung adaptor. Nilai default di bawah adalah
    # tebakan umum untuk adaptor "Twin USB Gamepad"; sesuaikan bila perlu.
    "control_buttons": {
        "toggle_mode": 8,        # Select -> switch Mouse/Gamepad
        "quit": 9,               # Start  -> keluar program
        "sens_up": 7,            # R1     -> naikkan sensitivitas
        "sens_down": 6,          # L1     -> turunkan sensitivitas
    },

    # Tombol yang dibebaskan (jangan dipakai dulu) untuk fitur besar nanti.
    "reserved_buttons": [2, 3],  # Square + Triangle

    # --- Fitur Voice-to-Text (lihat docs/VOICE_TO_TEXT_PLAN.md) ---
    "voice": {
        "enabled": True,
        "language": "id-ID",
        "toggle_button": 3,      # Kotak -> mulai/stop rekam
        "enter_button": 0,       # Segitiga -> tekan Enter
        "enter_hold_seconds": 0.0,  # 0 = langsung; >0 = perlu ditahan
        "freeze_mouse_while_recording": True,
        "auto_enter": False,
        "recognizer": "google",  # google | sphinx
        "typing_interval": 0.01,
        "overlay_enabled": True,
        "beep_enabled": True,
        "auto_boost_mic": True,   # naikkan volume mic saat startup (temuan V0)
    },

    "button_map": {
        "left_click": 0,         # Cross
        "right_click": 1,        # Circle
        # middle_click dinonaktifkan sementara (Square dibebaskan).
        "middle_click": -1,      # -1 = tidak aktif
    },
    "axis_map": {
        "cursor_x": 0,           # analog kiri X
        "cursor_y": 1,           # analog kiri Y
        "scroll_x": 2,           # analog kanan X
        "scroll_y": 3,           # analog kanan Y
    },
}

# Path default file config (di root proyek / di samping .exe)
DEFAULT_CONFIG_PATH = os.path.join(_app_dir(), "config.json")


# ---------------------------------------------------------------------------
# Dataclass konfigurasi
# ---------------------------------------------------------------------------

@dataclass
class ButtonMap:
    left_click: int = 0
    right_click: int = 1
    middle_click: int = -1


@dataclass
class AxisMap:
    cursor_x: int = 0
    cursor_y: int = 1
    scroll_x: int = 2
    scroll_y: int = 3


@dataclass
class ControlButtons:
    toggle_mode: int = 8
    quit: int = 9
    sens_up: int = 7
    sens_down: int = 6


@dataclass
class VoiceConfig:
    enabled: bool = True
    language: str = "id-ID"
    toggle_button: int = 3
    enter_button: int = 0
    enter_hold_seconds: float = 0.0
    freeze_mouse_while_recording: bool = True
    auto_enter: bool = False
    recognizer: str = "google"
    typing_interval: float = 0.01
    overlay_enabled: bool = True
    beep_enabled: bool = True
    auto_boost_mic: bool = True


@dataclass
class Config:
    joystick_index: int = 0
    deadzone: float = 0.15
    sensitivity: float = 12.0
    scroll_sensitivity: float = 1.0
    poll_interval_ms: int = 8
    invert_y: bool = False
    smoothing: float = 0.0
    sensitivity_step: float = 1.0
    sensitivity_min: float = 2.0
    sensitivity_max: float = 40.0
    startup_grace_seconds: float = 2.0
    control_buttons: ControlButtons = field(default_factory=ControlButtons)
    reserved_buttons: list[int] = field(default_factory=lambda: [2, 3])
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    button_map: ButtonMap = field(default_factory=ButtonMap)
    axis_map: AxisMap = field(default_factory=AxisMap)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Bangun Config dari dict, mengisi default bila field hilang."""
        merged = _deep_merge(DEFAULT_CONFIG, data or {})
        _validate(merged)

        return cls(
            joystick_index=int(merged["joystick_index"]),
            deadzone=float(merged["deadzone"]),
            sensitivity=float(merged["sensitivity"]),
            scroll_sensitivity=float(merged["scroll_sensitivity"]),
            poll_interval_ms=int(merged["poll_interval_ms"]),
            invert_y=bool(merged["invert_y"]),
            smoothing=float(merged["smoothing"]),
            sensitivity_step=float(merged["sensitivity_step"]),
            sensitivity_min=float(merged["sensitivity_min"]),
            sensitivity_max=float(merged["sensitivity_max"]),
            startup_grace_seconds=float(merged.get("startup_grace_seconds", 2.0)),
            control_buttons=ControlButtons(**merged["control_buttons"]),
            reserved_buttons=[int(b) for b in merged.get("reserved_buttons", [])],
            voice=VoiceConfig(**merged["voice"]),
            button_map=ButtonMap(**merged["button_map"]),
            axis_map=AxisMap(**merged["axis_map"]),
        )


# ---------------------------------------------------------------------------
# Fungsi bantu
# ---------------------------------------------------------------------------

def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Gabungkan dua dict secara rekursif (override menang)."""
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _validate(data: dict[str, Any]) -> None:
    """Validasi nilai config; lempar ValueError bila tidak masuk akal."""
    if not (0.0 <= data["deadzone"] < 1.0):
        raise ValueError("deadzone harus bernilai 0.0 <= x < 1.0")
    if data["sensitivity"] <= 0:
        raise ValueError("sensitivity harus > 0")
    if data["scroll_sensitivity"] < 0:
        raise ValueError("scroll_sensitivity tidak boleh negatif")
    if data["poll_interval_ms"] < 1:
        raise ValueError("poll_interval_ms minimal 1 ms")
    if not (0.0 <= data["smoothing"] < 1.0):
        raise ValueError("smoothing harus bernilai 0.0 <= x < 1.0")
    if data["sensitivity_step"] <= 0:
        raise ValueError("sensitivity_step harus > 0")
    if data["sensitivity_min"] <= 0:
        raise ValueError("sensitivity_min harus > 0")
    if data["sensitivity_max"] <= data["sensitivity_min"]:
        raise ValueError("sensitivity_max harus lebih besar dari sensitivity_min")
    if data["voice"]["recognizer"] not in ("google", "sphinx"):
        raise ValueError("voice.recognizer harus 'google' atau 'sphinx'")
    if data["voice"]["enter_hold_seconds"] < 0:
        raise ValueError("voice.enter_hold_seconds tidak boleh negatif")
    if data.get("startup_grace_seconds", 0) < 0:
        raise ValueError("startup_grace_seconds tidak boleh negatif")


def load_config(path: str | None = None, strict: bool = False) -> Config:
    """Muat config dari file JSON.

    Bila file tidak ada, config default akan dipakai dan file baru dibuat.
    Bila file rusak (JSON invalid / nilai tidak valid):
      - strict=True  -> lempar exception (dipakai saat startup agar jelas).
      - strict=False -> pakai default + cetak peringatan (dipakai saat hot-reload).
    """
    path = path or DEFAULT_CONFIG_PATH

    if not os.path.exists(path):
        default_cfg = Config.from_dict(DEFAULT_CONFIG)
        save_config(default_cfg, path)
        return default_cfg

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return Config.from_dict(data)
    except (json.JSONDecodeError, ValueError, TypeError, KeyError) as exc:
        if strict:
            raise
        print(f"[WARN] config.json bermasalah ({exc}). Memakai konfigurasi default.")
        return Config.from_dict(DEFAULT_CONFIG)


def save_config(cfg: Config, path: str | None = None) -> None:
    """Simpan config ke file JSON (dengan format rapi)."""
    path = path or DEFAULT_CONFIG_PATH
    data = {
        "joystick_index": cfg.joystick_index,
        "deadzone": cfg.deadzone,
        "sensitivity": cfg.sensitivity,
        "scroll_sensitivity": cfg.scroll_sensitivity,
        "poll_interval_ms": cfg.poll_interval_ms,
        "invert_y": cfg.invert_y,
        "smoothing": cfg.smoothing,
        "sensitivity_step": cfg.sensitivity_step,
        "sensitivity_min": cfg.sensitivity_min,
        "sensitivity_max": cfg.sensitivity_max,
        "startup_grace_seconds": cfg.startup_grace_seconds,
        "control_buttons": {
            "toggle_mode": cfg.control_buttons.toggle_mode,
            "quit": cfg.control_buttons.quit,
            "sens_up": cfg.control_buttons.sens_up,
            "sens_down": cfg.control_buttons.sens_down,
        },
        "reserved_buttons": list(cfg.reserved_buttons),
        "voice": {
            "enabled": cfg.voice.enabled,
            "language": cfg.voice.language,
            "toggle_button": cfg.voice.toggle_button,
            "enter_button": cfg.voice.enter_button,
            "enter_hold_seconds": cfg.voice.enter_hold_seconds,
            "freeze_mouse_while_recording": cfg.voice.freeze_mouse_while_recording,
            "auto_enter": cfg.voice.auto_enter,
            "recognizer": cfg.voice.recognizer,
            "typing_interval": cfg.voice.typing_interval,
            "overlay_enabled": cfg.voice.overlay_enabled,
            "beep_enabled": cfg.voice.beep_enabled,
            "auto_boost_mic": cfg.voice.auto_boost_mic,
        },
        "button_map": {
            "left_click": cfg.button_map.left_click,
            "right_click": cfg.button_map.right_click,
            "middle_click": cfg.button_map.middle_click,
        },
        "axis_map": {
            "cursor_x": cfg.axis_map.cursor_x,
            "cursor_y": cfg.axis_map.cursor_y,
            "scroll_x": cfg.axis_map.scroll_x,
            "scroll_y": cfg.axis_map.scroll_y,
        },
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
