"""Perekam audio dari mikrofon (manual start/stop).

Berbeda dari `speech_recognition.Microphone.listen()` yang blocking dan
auto-stop saat hening, kelas ini merekam di thread terpisah dan berhenti
hanya ketika diminta (meniru tombol toggle).
"""

from __future__ import annotations

import io
import threading
import wave

import pyaudio

RATE = 16000          # 16 kHz - cukup untuk speech recognition
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 1024


class AudioRecorder:
    """Merekam audio mikrofon di background thread."""

    def __init__(self, rate: int = RATE) -> None:
        self.rate = rate
        self._pa: pyaudio.PyAudio | None = None
        self._stream = None
        self._frames: list[bytes] = []
        self._thread: threading.Thread | None = None
        self._recording = False

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def frames_count(self) -> int:
        return len(self._frames)

    # -- Kontrol ------------------------------------------------------------

    def start(self) -> None:
        """Mulai merekam (non-blocking)."""
        if self._recording:
            return
        self._frames = []
        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=self.rate,
            input=True,
            frames_per_buffer=CHUNK,
        )
        self._recording = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def _record_loop(self) -> None:
        while self._recording:
            try:
                data = self._stream.read(CHUNK, exception_on_overflow=False)
                self._frames.append(data)
            except Exception:
                break

    def stop(self) -> bytes:
        """Hentikan rekaman; kembalikan data WAV (bytes)."""
        self._recording = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if self._pa is not None:
            try:
                self._pa.terminate()
            except Exception:
                pass
            self._pa = None

        return self._build_wav()

    def _build_wav(self) -> bytes:
        """Gabungkan frame menjadi file WAV di memori."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(CHANNELS)
            w.setsampwidth(2)  # 16-bit
            w.setframerate(self.rate)
            w.writeframes(b"".join(self._frames))
        buf.seek(0)
        return buf.read()

    def cancel(self) -> None:
        """Batalkan rekaman tanpa memproses (buang data)."""
        self._recording = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._pa is not None:
            try:
                self._pa.terminate()
            except Exception:
                pass
            self._pa = None
        self._frames = []
