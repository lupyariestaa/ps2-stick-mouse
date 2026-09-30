"""Logika pemetaan: deadzone, kurva kecepatan, dan konversi axis -> gerakan.

Modul ini murni perhitungan (tidak menyentuh hardware) sehingga mudah diuji.
"""

from __future__ import annotations

from dataclasses import dataclass


def _clamp(value: float, low: float, high: float) -> float:
    """Batasi nilai agar berada di antara low..high."""
    return max(low, min(high, value))


def apply_deadzone(value: float, deadzone: float) -> float:
    """Hilangkan nilai kecil di sekitar 0, dan skalakan ulang sisanya ke 0..1.

    Contoh: value=0.2, deadzone=0.15 -> hasil ~0.059 (bukan 0.2),
    sehingga transisi dari diam ke bergerak tetap halus.
    """
    if abs(value) <= deadzone:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    magnitude = (abs(value) - deadzone) / (1.0 - deadzone)
    return sign * magnitude


def apply_curve(value: float, exponent: float = 1.0) -> float:
    """Terapkan kurva non-linear agar kontrol lebih presisi di kecepatan rendah.

    exponent > 1 -> lebih halus di dekat 0 (default kontrol).
    exponent = 1 -> linier.
    """
    if value == 0.0:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    return sign * (abs(value) ** exponent)


@dataclass
class Smoother:
    """Smoothing sederhana (exponential moving average) per axis.

    factor = 0.0 -> tanpa smoothing (langsung).
    factor mendekati 1.0 -> makin halus namun makin lambat merespons.
    """

    factor: float = 0.0
    _x: float = 0.0
    _y: float = 0.0
    _initialized: bool = False

    def update(self, x: float, y: float) -> tuple[float, float]:
        if not self._initialized or self.factor <= 0.0:
            self._x, self._y = x, y
            self._initialized = True
            return self._x, self._y

        self._x = self._x * self.factor + x * (1.0 - self.factor)
        self._y = self._y * self.factor + y * (1.0 - self.factor)
        return self._x, self._y


class ScrollAccumulator:
    """Mengumpulkan nilai scroll kontinu menjadi notch diskret integer.

    Analog stick menghasilkan nilai kontinu, sementara roda mouse bergerak
    per notch. Accumulator menyimpan sisa nilai agar scroll terasa halus.
    """

    def __init__(self) -> None:
        self._x = 0.0
        self._y = 0.0

    def feed(self, dx: float, dy: float) -> tuple[int, int]:
        self._x += dx
        self._y += dy

        step_x = int(self._x)
        step_y = int(self._y)
        self._x -= step_x
        self._y -= step_y
        return step_x, step_y

    def reset(self) -> None:
        self._x = 0.0
        self._y = 0.0


class AxisMapper:
    """Mengubah nilai axis mentah menjadi delta gerakan kursor / scroll."""

    def __init__(
        self,
        deadzone: float,
        sensitivity: float,
        scroll_sensitivity: float = 1.0,
        curve_exponent: float = 1.6,
        invert_y: bool = False,
        smoothing: float = 0.0,
        sensitivity_min: float = 1.0,
        sensitivity_max: float = 100.0,
        sensitivity_step: float = 1.0,
    ) -> None:
        self.deadzone = deadzone
        self._sensitivity = sensitivity
        self.scroll_sensitivity = scroll_sensitivity
        self.curve_exponent = curve_exponent
        self.invert_y = invert_y
        self.sensitivity_min = sensitivity_min
        self.sensitivity_max = sensitivity_max
        self.sensitivity_step = sensitivity_step
        self._smoother = Smoother(factor=smoothing)
        self._scroll_accum = ScrollAccumulator()

    # -- Sensitivitas runtime (diubah lewat L1/R1) -------------------------

    @property
    def sensitivity(self) -> float:
        return self._sensitivity

    @sensitivity.setter
    def sensitivity(self, value: float) -> None:
        self._sensitivity = _clamp(value, self.sensitivity_min, self.sensitivity_max)

    def increase_sensitivity(self) -> float:
        """Naikkan sensitivitas selangkah (clamped). Kembalikan nilai baru."""
        self._sensitivity = _clamp(
            self._sensitivity + self.sensitivity_step,
            self.sensitivity_min,
            self.sensitivity_max,
        )
        return self._sensitivity

    def decrease_sensitivity(self) -> float:
        """Turunkan sensitivitas selangkah (clamped). Kembalikan nilai baru."""
        self._sensitivity = _clamp(
            self._sensitivity - self.sensitivity_step,
            self.sensitivity_min,
            self.sensitivity_max,
        )
        return self._sensitivity

    def cursor_delta(self, raw_x: float, raw_y: float) -> tuple[int, int]:
        """Hitung delta gerak kursor (piksel) dari axis analog mentah."""
        x = apply_deadzone(raw_x, self.deadzone)
        y = apply_deadzone(raw_y, self.deadzone)

        x = apply_curve(x, self.curve_exponent)
        y = apply_curve(y, self.curve_exponent)

        x, y = self._smoother.update(x, y)

        if self.invert_y:
            y = -y

        return int(round(x * self.sensitivity)), int(round(y * self.sensitivity))

    def scroll_delta(self, raw_x: float, raw_y: float) -> tuple[int, int]:
        """Hitung delta scroll (notch roda mouse) dari axis analog mentah.

        Scroll wheel bekerja dalam satuan diskret (biasanya 1 notch), sehingga
        nilai kontinu dari analog dikumpulkan (accumulate) lalu dibulatkan.
        """
        x = apply_deadzone(raw_x, self.deadzone)
        y = apply_deadzone(raw_y, self.deadzone)

        # Untuk scroll, arah Y biasanya dibalik (dorong ke atas = scroll ke atas).
        sx = x * self.scroll_sensitivity
        sy = -y * self.scroll_sensitivity

        return self._scroll_accum.feed(sx, sy)

    def reset_scroll(self) -> None:
        """Bersihkan sisa akumulasi scroll (mis. saat ganti mode)."""
        self._scroll_accum.reset()
