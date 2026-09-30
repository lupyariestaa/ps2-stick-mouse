"""Pengenalan suara (Speech-to-Text).

Mendukung dua engine:
- "google"  : Google Web Speech API (online, akurasi tinggi).
- "sphinx"  : PocketSphinx (offline, perlu install tambahan).
- "sapi"    : Windows SAPI via speech_recognition? (tidak langsung didukung)
              -> fallback memakai windows_sapi module (lihat voice.sapi).
"""

from __future__ import annotations

import speech_recognition as sr


class RecognitionError(RuntimeError):
    """Kesalahan umum saat pengenalan suara."""


class NoSpeechError(RecognitionError):
    """Tidak ada suara yang bisa dikenali."""


class NetworkError(RecognitionError):
    """Gagal menghubungi layanan online."""


class Recognizer:
    """Wrapper speech_recognition untuk mengenali audio WAV (bytes)."""

    def __init__(self, language: str = "id-ID", engine: str = "google") -> None:
        self.language = language
        self.engine = engine
        self._r = sr.Recognizer()

    def recognize(self, wav_bytes: bytes) -> str:
        """Kenali audio WAV (bytes) -> teks.

        Melempar NoSpeechError bila tidak ada suara, NetworkError bila gagal
        koneksi, RecognitionError untuk kesalahan lain.
        """
        import io

        with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
            audio = self._r.record(source)

        try:
            if self.engine == "sphinx":
                return self._r.recognize_sphinx(audio, language=self.language)
            return self._r.recognize_google(audio, language=self.language)
        except sr.UnknownValueError as exc:
            raise NoSpeechError("Suara tidak dapat dikenali.") from exc
        except sr.RequestError as exc:
            raise NetworkError(f"Gagal menghubungi layanan STT: {exc}") from exc
        except Exception as exc:
            raise RecognitionError(str(exc)) from exc
