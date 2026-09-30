"""Controller: orkestrasi input stik -> aksi mouse.

Memisahkan logika inti dari main loop sehingga mudah diuji dan dipelihara.
Menangani:
- Mode Manager (MOUSE / GAMEPAD) + toggle via tombol Select
- Tombol Start untuk keluar program
- L1/R1 untuk mengatur sensitivitas kursor secara real-time
- Pergerakan kursor
- Scroll (analog kanan)
- Klik (tombol PS2 -> klik kiri/kanan) dengan edge-trigger
- Voice-to-text: Kotak = toggle rekam, Segitiga (tahan) = Enter
- Pelepasan tombol aman saat ganti mode
"""

from __future__ import annotations

import time

from pynput.mouse import Button

from .config import Config
from .joystick_input import JoystickReader
from .mapping import AxisMapper
from .mode_manager import Mode, ModeManager
from .mouse_actuator import MouseActuator
from .voice.voice_manager import VoiceManager, VoiceState

# Pemetaan nama aksi -> tombol pynput
_BUTTONS = {
    "left_click": Button.left,
    "right_click": Button.right,
    "middle_click": Button.middle,
}


class Controller:
    """Menghubungkan stik dan mouse berdasarkan config & mode aktif."""

    def __init__(
        self,
        cfg: Config,
        reader: JoystickReader,
        mouse: MouseActuator,
        mode: ModeManager,
    ) -> None:
        self._cfg = cfg
        self._reader = reader
        self._mouse = mouse
        self._mode = mode
        self._mapper = self._build_mapper(cfg)

        # Status tombol sebelumnya (untuk edge-trigger)
        self._prev_buttons: dict[str, bool] = {name: False for name in _BUTTONS}
        self._prev_control: dict[str, bool] = {
            "toggle_mode": False,
            "quit": False,
            "sens_up": False,
            "sens_down": False,
            "voice_toggle": False,
            "enter": False,
        }

        # Flag: pengguna minta keluar (dibaca oleh main loop)
        self._quit_requested = False

        # Grace period agar tombol tidak false-trigger saat startup.
        self._start_time = time.monotonic()
        self._grace_period = cfg.startup_grace_seconds

        # -- Voice-to-text --------------------------------------------------
        self._voice: VoiceManager | None = None
        self._voice_enabled = cfg.voice.enabled
        self._enter_press_time: float | None = None
        self._overlay = None  # di-set dari luar via set_overlay()
        if self._voice_enabled:
            self._build_voice(cfg)

    # -- Properti -------------------------------------------

    @property
    def quit_requested(self) -> bool:
        return self._quit_requested

    @property
    def sensitivity(self) -> float:
        return self._mapper.sensitivity

    @property
    def mode_name(self) -> str:
        return self._mode.mode.value

    def request_quit(self) -> None:
        """Minta main loop berhenti (dipakai tray / shutdown)."""
        self._quit_requested = True

    def toggle_mode(self) -> str:
        """Ganti mode secara programatik. Kembalikan nama mode baru."""
        self._mouse.release_all()
        self._mapper.reset_scroll()
        new_mode = self._mode.toggle()
        return new_mode.value

    # -- Manajemen config -----------------------------------

    @staticmethod
    def _build_mapper(cfg: Config) -> AxisMapper:
        return AxisMapper(
            deadzone=cfg.deadzone,
            sensitivity=cfg.sensitivity,
            scroll_sensitivity=cfg.scroll_sensitivity,
            invert_y=cfg.invert_y,
            smoothing=cfg.smoothing,
            sensitivity_min=cfg.sensitivity_min,
            sensitivity_max=cfg.sensitivity_max,
            sensitivity_step=cfg.sensitivity_step,
        )

    def apply_config(self, cfg: Config) -> None:
        """Terapkan config baru (dipakai saat hot-reload)."""
        old_sensitivity = self._mapper.sensitivity
        self._cfg = cfg
        self._mapper = self._build_mapper(cfg)
        # Pertahankan sensitivitas yang sudah disesuaikan runtime bila masih valid.
        self._mapper.sensitivity = old_sensitivity

    def set_reader(self, reader: JoystickReader) -> None:
        """Ganti sumber reader (dipakai saat reconnect setelah stik dicabut)."""
        self._reader = reader
        self._prev_buttons = {name: False for name in _BUTTONS}
        self._prev_control = {name: False for name in self._prev_control}

    # -- Siklus utama ---------------------------------------

    def update(self) -> None:
        """Proses satu frame input -> aksi."""
        self._reader.pump()

        # Grace period: abaikan semua tombol beberapa saat setelah startup
        # untuk mencegah false-trigger (mis. tombol Start terdeteksi "ditekan"
        # saat stik baru diinisialisasi).
        if time.monotonic() - self._start_time < self._grace_period:
            self._sync_button_states()
            return

        self._handle_control_buttons()
        if self._voice_enabled and self._voice is not None:
            self._handle_voice_buttons()

        # Bila voice sedang merekam/memproses dan config meminta freeze,
        # jangan gerakkan mouse; cukup pastikan tidak ada tombol tertahan.
        freeze = (
            self._voice_active_freeze()
            if self._voice is not None
            else False
        )

        if freeze:
            self._release_click_buttons()
            return

        if self._mode.is_mouse:
            self._update_mouse()
        else:
            # GAMEPAD mode: pastikan tidak ada tombol mouse yang tertahan.
            self._release_click_buttons()

    def _voice_active_freeze(self) -> bool:
        """Apakah mouse harus di-freeze karena voice aktif?"""
        if self._voice is None:
            return False
        return self._cfg.voice.freeze_mouse_while_recording and self._voice.is_active

    # -- Tombol kontrol (Select/Start/L1/R1) ----------------

    def _handle_control_buttons(self) -> None:
        cb = self._cfg.control_buttons

        # 1) Select -> toggle mode (edge-triggered)
        if self._edge("toggle_mode", self._reader.button(cb.toggle_mode)):
            self._mouse.release_all()
            self._mapper.reset_scroll()
            new_mode = self._mode.toggle()
            print(f"[MODE] Beralih ke {new_mode.value}")

        # 2) Start -> minta keluar
        if self._edge("quit", self._reader.button(cb.quit)):
            print("[INFO] Tombol Start ditekan - keluar program.")
            self._quit_requested = True

        # 3) L1 -> turunkan sensitivitas
        if self._edge("sens_down", self._reader.button(cb.sens_down)):
            value = self._mapper.decrease_sensitivity()
            print(f"[SENS] Sensitivitas diturunkan -> {value:.1f}")

        # 4) R1 -> naikkan sensitivitas
        if self._edge("sens_up", self._reader.button(cb.sens_up)):
            value = self._mapper.increase_sensitivity()
            print(f"[SENS] Sensitivitas dinaikkan -> {value:.1f}")

    def _edge(self, key: str, down: bool) -> bool:
        """Deteksi transisi lepas -> ditekan untuk tombol kontrol."""
        triggered = down and not self._prev_control[key]
        self._prev_control[key] = down
        return triggered

    def _sync_button_states(self) -> None:
        """Sinkronkan status tombol tanpa memicu aksi (saat grace period)."""
        cb = self._cfg.control_buttons
        self._prev_control["toggle_mode"] = self._reader.button(cb.toggle_mode)
        self._prev_control["quit"] = self._reader.button(cb.quit)
        self._prev_control["sens_up"] = self._reader.button(cb.sens_up)
        self._prev_control["sens_down"] = self._reader.button(cb.sens_down)
        if self._voice_enabled:
            vc = self._cfg.voice
            self._prev_control["voice_toggle"] = self._reader.button(vc.toggle_button)
        # Sinkronkan tombol klik juga.
        bm = self._cfg.button_map
        self._prev_buttons["left_click"] = (
            self._reader.button(bm.left_click) if bm.left_click >= 0 else False
        )
        self._prev_buttons["right_click"] = (
            self._reader.button(bm.right_click) if bm.right_click >= 0 else False
        )

    # -- Voice-to-text --------------------------------------

    def _build_voice(self, cfg: Config) -> None:
        """Bangun VoiceManager berdasarkan config."""
        self._voice = VoiceManager(
            language=cfg.voice.language,
            engine=cfg.voice.recognizer,
            typing_interval=cfg.voice.typing_interval,
            auto_enter=cfg.voice.auto_enter,
            beep_enabled=cfg.voice.beep_enabled,
            on_state_change=self._on_voice_state,
        )

    def _on_voice_state(self, state: VoiceState) -> None:
        """Callback saat state voice berubah (dipakai overlay)."""
        if self._overlay is None:
            return
        if state is VoiceState.RECORDING:
            self._overlay.show(self._mouse.position)
        else:
            self._overlay.hide()

    @property
    def voice(self) -> VoiceManager | None:
        return self._voice

    def set_overlay(self, overlay) -> None:
        """Set objek overlay (MicOverlay atau None)."""
        self._overlay = overlay

    @property
    def voice_active(self) -> bool:
        """True bila voice sedang merekam/memproses (mouse harus freeze)."""
        return self._voice is not None and self._voice.is_active

    def _handle_voice_buttons(self) -> None:
        vc = self._cfg.voice

        # Voice hanya aktif di MOUSE mode (cegah konflik dengan gamepad / game).
        if not self._mode.is_mouse:
            # Reset status agar tidak "nyangkut" saat kembali ke mouse mode.
            self._prev_control["voice_toggle"] = self._reader.button(vc.toggle_button)
            self._prev_control["enter"] = self._reader.button(vc.enter_button)
            self._enter_press_time = None
            return

        # 1) Tombol Kotak -> toggle rekam (edge-triggered)
        if self._edge("voice_toggle", self._reader.button(vc.toggle_button)):
            self._voice.toggle()

        # 2) Tombol Segitiga -> tekan Enter
        #    - Bila enter_hold_seconds <= 0: langsung (edge-triggered).
        #    - Bila > 0: harus ditahan selama itu agar terpicu.
        enter_down = self._reader.button(vc.enter_button)
        if vc.enter_hold_seconds <= 0:
            # Mode langsung: pakai edge-trigger biasa.
            if self._edge("enter", enter_down):
                self._voice.press_enter()
                print("[VOICE] Enter ditekan.")
        else:
            # Mode tahan (hold).
            now = time.monotonic()
            if enter_down:
                if self._enter_press_time is None:
                    self._enter_press_time = now
                elif (
                    self._enter_press_time >= 0
                    and now - self._enter_press_time >= vc.enter_hold_seconds
                ):
                    self._voice.press_enter()
                    print("[VOICE] Enter ditekan.")
                    self._enter_press_time = -1.0
            else:
                self._enter_press_time = None

    def shutdown(self) -> None:
        """Bersihkan sumber daya (voice) saat program keluar."""
        if self._voice is not None:
            self._voice.shutdown()

    # -- Aksi mode mouse ------------------------------------

    def _update_mouse(self) -> None:
        am = self._cfg.axis_map

        # Gerakkan kursor
        dx, dy = self._mapper.cursor_delta(
            self._reader.axis(am.cursor_x),
            self._reader.axis(am.cursor_y),
        )
        self._mouse.move(dx, dy)

        # Scroll via analog kanan
        sx, sy = self._mapper.scroll_delta(
            self._reader.axis(am.scroll_x),
            self._reader.axis(am.scroll_y),
        )
        self._mouse.scroll(sx, sy)

        # Klik (edge-triggered)
        self._update_click_buttons()

    def _update_click_buttons(self) -> None:
        bm = self._cfg.button_map
        mapping = {
            "left_click": bm.left_click,
            "right_click": bm.right_click,
            "middle_click": bm.middle_click,
        }
        for name, button_id in mapping.items():
            # button_id < 0 -> dinonaktifkan (mis. middle_click = -1)
            if button_id < 0:
                continue
            down = self._reader.button(button_id)
            was_down = self._prev_buttons[name]
            if down and not was_down:
                self._mouse.press(_BUTTONS[name])
            elif not down and was_down:
                self._mouse.release(_BUTTONS[name])
            self._prev_buttons[name] = down

    def _release_click_buttons(self) -> None:
        """Lepas semua tombol klik & reset status (dipakai saat keluar MOUSE mode)."""
        for name in _BUTTONS:
            if self._prev_buttons[name]:
                self._mouse.release(_BUTTONS[name])
                self._prev_buttons[name] = False
