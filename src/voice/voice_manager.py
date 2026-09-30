"""VoiceManager: state machine untuk fitur voice-to-text.

State:
    IDLE       - tidak merekam, mouse aktif normal.
    RECORDING  - merekam audio, overlay mic tampil, mouse di-freeze.
    PROCESSING - audio dikirim ke STT & teks diketik, mouse tetap freeze.

Pemrosesan (STT) dijalankan di thread terpisah agar main loop stik tetap
responsif (bisa mendeteksi tombol stop, dll).
"""

from __future__ import annotations

import threading
from enum import Enum
from typing import Callable

from . import beeper
from .recorder import AudioRecorder
from .recognizer import NetworkError, NoSpeechError, RecognitionError, Recognizer
from .typer import TextTyper


class VoiceState(Enum):
    IDLE = "IDLE"
    RECORDING = "RECORDING"
    PROCESSING = "PROCESSING"


class VoiceManager:
    """Mengatur siklus hidup fitur voice-to-text."""

    def __init__(
        self,
        language: str = "id-ID",
        engine: str = "google",
        typing_interval: float = 0.01,
        auto_enter: bool = False,
        beep_enabled: bool = True,
        on_state_change: Callable[[VoiceState], None] | None = None,
    ) -> None:
        self._state = VoiceState.IDLE
        self._language = language
        self._engine = engine
        self._typer = TextTyper(interval=typing_interval)
        self._recorder = AudioRecorder()
        self._recognizer = Recognizer(language=language, engine=engine)
        self._auto_enter = auto_enter
        self._beep_enabled = beep_enabled
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._on_state_change = on_state_change
        self.last_text: str = ""
        self.enabled = True

    def _beep_start(self) -> None:
        if self._beep_enabled:
            beeper.beep_start()

    def _beep_stop(self) -> None:
        if self._beep_enabled:
            beeper.beep_stop()

    def _beep_error(self) -> None:
        if self._beep_enabled:
            beeper.beep_error()

    # -- Properti -----------------------------------------------------------

    @property
    def state(self) -> VoiceState:
        return self._state

    @property
    def is_active(self) -> bool:
        """True bila sedang RECORDING atau PROCESSING (mouse harus di-freeze)."""
        return self._state is not VoiceState.IDLE

    @property
    def is_recording(self) -> bool:
        return self._state is VoiceState.RECORDING

    # -- Kontrol ------------------------------------------------------------

    def set_state(self, state: VoiceState) -> None:
        with self._lock:
            self._state = state
        if self._on_state_change is not None:
            try:
                self._on_state_change(state)
            except Exception:
                pass

    def toggle(self) -> None:
        """Dipanggil saat tombol Kotak ditekan."""
        if not self.enabled:
            return

        if self._state is VoiceState.IDLE:
            self._start_recording()
        elif self._state is VoiceState.RECORDING:
            self._stop_and_process()
        # Bila PROCESSING: abaikan (cegah spam tombol).

    def press_enter(self) -> None:
        """Tekan Enter (berdiri sendiri, tidak terikat state voice)."""
        try:
            self._typer.press_enter()
        except Exception:
            pass

    def shutdown(self) -> None:
        """Bersihkan sumber daya saat program keluar."""
        if self._recorder.is_recording:
            self._recorder.cancel()

    # -- Internal -----------------------------------------------------------

    def _start_recording(self) -> None:
        try:
            self._recorder.start()
        except Exception as exc:
            print(f"[VOICE] Gagal mulai merekam: {exc}")
            self._beep_error()
            return
        self.set_state(VoiceState.RECORDING)
        self._beep_start()
        print("[VOICE] Merekam... (tekan Kotak lagi untuk berhenti)")

    def _stop_and_process(self) -> None:
        wav = self._recorder.stop()
        self._beep_stop()
        self.set_state(VoiceState.PROCESSING)
        print("[VOICE] Memproses...")

        # Proses STT + ketik di thread terpisah.
        self._thread = threading.Thread(target=self._process, args=(wav,), daemon=True)
        self._thread.start()

    def _process(self, wav: bytes) -> None:
        try:
            text = self._recognizer.recognize(wav)
            self.last_text = text
            print(f"[VOICE] Hasil: '{text}'")
            self._typer.type_text(text)
            if self._auto_enter:
                self._typer.press_enter()
        except NoSpeechError:
            print("[VOICE] Tidak ada suara terdeteksi.")
            self._beep_error()
        except NetworkError as exc:
            print(f"[VOICE] Gagal (jaringan): {exc}")
            self._beep_error()
        except RecognitionError as exc:
            print(f"[VOICE] Gagal: {exc}")
            self._beep_error()
        finally:
            self.set_state(VoiceState.IDLE)
