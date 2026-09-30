"""Entry point utama: menghubungkan pembacaan stik dengan aksi mouse.

Jalankan:
    .venv\\Scripts\\python.exe -u -m src.main
atau:
    .venv\\Scripts\\python.exe src\\main.py
"""

from __future__ import annotations

import time

from .config import Config, load_config, DEFAULT_CONFIG_PATH
from .config_watcher import ConfigWatcher
from .controller import Controller
from .joystick_input import JoystickNotFoundError, JoystickReader
from .mode_manager import Mode, ModeManager
from .mouse_actuator import MouseActuator
from .tray import TrayIcon

# Berapa lama menunggu sebelum mencoba reconnect ke stik (detik)
_RECONNECT_INTERVAL = 1.0


def _print_banner(
    cfg: Config, reader: JoystickReader, hot_reload: bool, tray: bool
) -> None:
    print("=" * 56)
    print("  Stick PS2 -> Mouse  (FASE 3 + Voice)")
    print("=" * 56)
    print(f"  Stik          : {reader.name} (index {reader.index})")
    print(f"  Axes/Buttons  : {reader.num_axes} / {reader.num_buttons}")
    print(f"  Deadzone      : {cfg.deadzone}")
    print(f"  Sensitivity   : {cfg.sensitivity} (atur via L1/R1)")
    print(f"  Scroll sens   : {cfg.scroll_sensitivity}")
    print(f"  Select        : toggle Mouse/Gamepad")
    print(f"  Start         : keluar program")
    if cfg.voice.enabled:
        print(f"  Kotak         : voice-to-text (mulai/stop)")
        if cfg.voice.enter_hold_seconds > 0:
            print(f"  Segitiga (tahan {cfg.voice.enter_hold_seconds}s): tekan Enter")
        else:
            print(f"  Segitiga      : tekan Enter")
        print(f"  Voice bahasa  : {cfg.voice.language}")
    print(f"  Hot-reload    : {'aktif' if hot_reload else 'tidak aktif'}")
    print(f"  Tray icon     : {'aktif' if tray else 'tidak aktif'}")
    print("-" * 56)
    print("  Mode awal: MOUSE")
    print("  Tekan Ctrl+C di terminal untuk keluar.")
    print("=" * 56, flush=True)


def _connect(cfg: Config) -> JoystickReader | None:
    """Coba hubungkan ke stik; kembalikan None bila gagal (tanpa crash)."""
    try:
        return JoystickReader(cfg.joystick_index)
    except JoystickNotFoundError:
        return None


def run() -> None:
    cfg = load_config()

    reader = _connect(cfg)
    if reader is None:
        print(f"[ERROR] Stik index {cfg.joystick_index} tidak ditemukan.")
        print("[INFO] Colok stik lalu jalankan ulang program.")
        return

    mouse = MouseActuator()
    mode = ModeManager(Mode.MOUSE)
    controller = Controller(cfg, reader, mouse, mode)

    # -- Auto-boost volume mikrofon (temuan FASE V0) ------------------------
    if cfg.voice.enabled and cfg.voice.auto_boost_mic:
        from .voice.mic_boost import boost_microphone_volume

        n = boost_microphone_volume(1.0)
        if n > 0:
            print(f"[VOICE] Volume audio di-boost ke 100% ({n} device).")

    # -- Overlay ikon mic (opsional) ----------------------------------------
    overlay = None
    if cfg.voice.enabled and cfg.voice.overlay_enabled:
        from .voice.overlay import MicOverlay

        overlay = MicOverlay()
        if overlay.enabled:
            overlay.start()
            controller.set_overlay(overlay)

    # -- Hot-reload config --------------------------------------------------
    def _reload() -> None:
        try:
            new_cfg = load_config()
        except Exception as exc:
            print(f"[WARN] Config tidak valid, diabaikan: {exc}")
            return
        nonlocal cfg
        cfg = new_cfg
        controller.apply_config(new_cfg)
        print("[CONFIG] Config dimuat ulang.")

    watcher = ConfigWatcher(DEFAULT_CONFIG_PATH, _reload)
    watcher.start()

    # -- Tray icon (opsional) ----------------------------------------------
    def _status_text() -> str:
        return (
            f"Mode: {controller.mode_name} | "
            f"Sens: {controller.sensitivity:.1f}"
        )

    tray = TrayIcon(
        on_quit=controller.request_quit,
        on_toggle_mode=lambda: print(f"[MODE] (tray) {controller.toggle_mode()}"),
        get_status=_status_text,
    )
    tray.start()

    _print_banner(cfg, reader, watcher.enabled, tray.enabled)

    interval = cfg.poll_interval_ms / 1000.0
    last_reconnect_attempt = 0.0

    try:
        while True:
            try:
                controller.update()
                if controller.quit_requested:
                    break
            except Exception as exc:  # stik dicabut / error pygame
                # Coba lepas semua tombol agar tidak "nyangkut".
                mouse.release_all()

                now = time.monotonic()
                if now - last_reconnect_attempt >= _RECONNECT_INTERVAL:
                    last_reconnect_attempt = now
                    print(f"\n[WARN] Koneksi stik terputus ({exc}).")
                    print("[INFO] Menunggu stik terhubung kembali...")
                    try:
                        reader.close()
                    except Exception:
                        pass
                    reader = _connect(cfg)
                    if reader is not None:
                        controller.set_reader(reader)
                        print(f"[INFO] Stik tersambung kembali: {reader.name}")
                    else:
                        time.sleep(_RECONNECT_INTERVAL)
                continue

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n[INFO] Dihentikan oleh pengguna.")
    finally:
        tray.stop()
        watcher.stop()
        controller.shutdown()
        if overlay is not None:
            overlay.stop()
        mouse.release_all()
        try:
            reader.close()
        except Exception:
            pass
        print("[INFO] Selesai. Sumber daya dibebaskan.")


def main() -> None:
    run()


if __name__ == "__main__":
    main()
