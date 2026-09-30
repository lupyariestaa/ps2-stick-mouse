"""Skrip diagnostik stik (T1.1 & T1.2).

Menampilkan seluruh stik yang terdeteksi, lalu memantau nilai axis dan index
tombol secara real-time. Berguna untuk memetakan tombol PS2 ke index pygame.

Jalankan:
    .venv\\Scripts\\python.exe -m src.diagnose
    .venv\\Scripts\\python.exe -m src.diagnose 1     # pantau stik index 1
"""

from __future__ import annotations

import json
import sys
import time

from .config import DEFAULT_CONFIG_PATH
from .joystick_input import list_joysticks
from .joystick_input import JoystickReader, JoystickNotFoundError

# Tombol-tombol yang akan dipandu saat mode wizard (berdasarkan fisik stik PS2).
# Format: (label yang ditampilkan, nama field di config / keterangan)
WIZARD_BUTTONS = [
    ("X (Cross)", "left_click"),
    ("Bulat (Circle)", "right_click"),
    ("Kotak (Square)", "square_reserved"),
    ("Segitiga (Triangle)", "triangle_reserved"),
    ("L1", "sens_down"),
    ("R1", "sens_up"),
    ("Select", "toggle_mode"),
    ("Start", "quit"),
]


def show_devices() -> None:
    print("=" * 56)
    print("  STIK YANG TERDETEKSI (T1.1)")
    print("=" * 56)
    devices = list_joysticks()
    if not devices:
        print("  (tidak ada stik terdeteksi)")
        print("=" * 56)
        return
    for d in devices:
        print(f"  [{d['index']}] {d['name']}")
        print(f"       axes={d['axes']}  buttons={d['buttons']}  hats={d['hats']}")
    print("=" * 56)


def monitor(index: int) -> None:
    try:
        reader = JoystickReader(index)
    except JoystickNotFoundError as exc:
        print(f"[ERROR] {exc}")
        return

    print()
    print("=" * 56)
    print(f"  MONITOR REAL-TIME (T1.2) - {reader.name} [index {index}]")
    print("=" * 56)
    print("  Gerakkan analog & tekan tombol. Tekan Ctrl+C untuk berhenti.")
    print("  Cetak index tombol yang muncul untuk mengisi config.json.")
    print("=" * 56)

    prev_buttons = [False] * reader.num_buttons
    prev_hat = (0, 0)

    try:
        while True:
            reader.pump()

            axes = [reader.axis(i) for i in range(reader.num_axes)]
            axes_str = " ".join(f"A{i}={v:+.2f}" for i, v in enumerate(axes))

            # Deteksi perubahan tombol (press/release) untuk log yang jelas.
            for i in range(reader.num_buttons):
                now = reader.button(i)
                if now and not prev_buttons[i]:
                    print(f"  [BUTTON] index {i} DITEKAN")
                elif not now and prev_buttons[i]:
                    print(f"  [BUTTON] index {i} dilepas")
                prev_buttons[i] = now

            hat = reader.hat(0) if reader.num_hats else (0, 0)
            if hat != prev_hat:
                print(f"  [HAT] {prev_hat} -> {hat}")
                prev_hat = hat

            sys.stdout.write(f"\r{axes_str} | hats={hat}          ")
            sys.stdout.flush()

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n[INFO] Monitoring dihentikan.")
    finally:
        reader.close()


def wizard(index: int) -> None:
    """Pandu pengguna menekan tiap tombol untuk mencatat index-nya.

    Menghasilkan peta label fisik -> index tombol, lalu menawarkan untuk
    menyimpan hasilnya ke config.json.
    """
    try:
        reader = JoystickReader(index)
    except JoystickNotFoundError as exc:
        print(f"[ERROR] {exc}")
        return

    print()
    print("=" * 56)
    print(f"  WIZARD PEMETAAN TOMBOL - {reader.name} [index {index}]")
    print("=" * 56)
    print("  Ikuti instruksi. Tekan tombol yang diminta SATU KALI,")
    print("  lalu lepaskan. (Bisa juga tekan 'q' lalu Enter untuk batal.)")
    print("=" * 56)
    print()

    mapping: dict[str, int] = {}

    try:
        for label, field in WIZARD_BUTTONS:
            print(f"  >> Tekan tombol: {label}")
            captured = _wait_for_press(reader)
            if captured is None:
                print("\n[INFO] Dibatalkan oleh pengguna.")
                return
            mapping[field] = captured
            print(f"     Tertangkap: index {captured}\n")

    finally:
        reader.close()

    # -- Ringkasan hasil ---------------------------------------------------
    print("=" * 56)
    print("  HASIL PEMETAAN")
    print("=" * 56)
    for label, field in WIZARD_BUTTONS:
        print(f"  {label:<18} -> index {mapping[field]}")
    print("=" * 56)

    # -- Tawarkan update ke config ----------------------------------------
    answer = input("\nUpdate config.json dengan pemetaan ini? (y/n): ").strip().lower()
    if answer != "y":
        print("[INFO] Tidak ada perubahan. Salin manual bila perlu:")
        print(json.dumps(mapping, indent=2))
        return

    _apply_to_config(mapping)
    print("[OK] config.json berhasil diperbarui!")


def _wait_for_press(reader: JoystickReader) -> int | None:
    """Tunggu sampai ada tombol ditekan; kembalikan index-nya.

    Kembalikan None bila pengguna membatalkan (mengetik 'q').
    """
    # Pastikan semua tombol lepas dulu (hindari deteksi tombol yang masih ditahan).
    while _any_pressed(reader):
        reader.pump()
        time.sleep(0.02)

    while True:
        reader.pump()
        for i in range(reader.num_buttons):
            if reader.button(i):
                # Tunggu sampai tombol dilepas agar tidak dobel.
                while reader.button(i):
                    reader.pump()
                    time.sleep(0.02)
                return i
        time.sleep(0.02)


def _any_pressed(reader: JoystickReader) -> bool:
    return any(reader.button(i) for i in range(reader.num_buttons))


def _apply_to_config(mapping: dict[str, int]) -> None:
    """Update config.json berdasarkan hasil wizard (menjaga nilai lain)."""
    from .config import load_config

    cfg = load_config()
    data = json.loads(json.dumps(_config_to_dict(cfg)))  # salinan

    # Tombol klik
    if "left_click" in mapping:
        data["button_map"]["left_click"] = mapping["left_click"]
    if "right_click" in mapping:
        data["button_map"]["right_click"] = mapping["right_click"]

    # Tombol kontrol
    if "toggle_mode" in mapping:
        data["control_buttons"]["toggle_mode"] = mapping["toggle_mode"]
    if "quit" in mapping:
        data["control_buttons"]["quit"] = mapping["quit"]
    if "sens_up" in mapping:
        data["control_buttons"]["sens_up"] = mapping["sens_up"]
    if "sens_down" in mapping:
        data["control_buttons"]["sens_down"] = mapping["sens_down"]

    # Tombol reserved (Square & Triangle)
    reserved = []
    if "square_reserved" in mapping:
        reserved.append(mapping["square_reserved"])
    if "triangle_reserved" in mapping:
        reserved.append(mapping["triangle_reserved"])
    if reserved:
        data["reserved_buttons"] = reserved

    with open(DEFAULT_CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def _config_to_dict(cfg) -> dict:
    """Konversi Config dataclass -> dict untuk keperluan edit JSON."""
    return {
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


def main() -> None:
    show_devices()
    index = 0
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    if args:
        try:
            index = int(args[0])
        except ValueError:
            print(f"[WARN] Argumen '{args[0]}' bukan angka, memakai index 0.")

    # Mode wizard: `python -m src.diagnose wizard`
    if "wizard" in sys.argv:
        if sys.stdin.isatty():
            input("\nTekan Enter untuk memulai wizard...")
        wizard(index)
        return

    # Mode monitor biasa
    if sys.stdin.isatty():
        input("\nTekan Enter untuk mulai monitoring...")
    monitor(index)


if __name__ == "__main__":
    main()
