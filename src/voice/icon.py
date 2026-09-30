"""Generator ikon mikrofon (PNG) untuk overlay.

Membuat ikon mic sederhana memakai Pillow, sehingga tidak butuh file gambar
eksternal. File hasil disimpan di `assets/mic.png` (dan bisa diganti manual
oleh pengguna - lihat assets/README.md).
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

# Path folder assets (di root proyek / di samping .exe)
import sys


def _assets_dir() -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base, "assets")
    os.makedirs(path, exist_ok=True)
    return path


def create_mic_icon(size: int = 96, color=(220, 60, 60)) -> "Image.Image":
    """Buat ikon mikrofon sederhana."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    cx = size // 2
    # Badan mic (kapsul)
    body_w = size * 0.22
    body_top = size * 0.18
    body_bottom = size * 0.58
    d.rounded_rectangle(
        [cx - body_w / 2, body_top, cx + body_w / 2, body_bottom],
        radius=body_w / 2,
        fill=color,
    )
    # Bracket (busa luar)
    br = size * 0.26
    d.arc(
        [cx - br, size * 0.36, cx + br, size * 0.36 + br * 2],
        start=0,
        end=180,
        fill=color,
        width=max(2, int(size * 0.05)),
    )
    # Tangkai
    d.line(
        [cx, size * 0.72, cx, size * 0.84],
        fill=color,
        width=max(2, int(size * 0.05)),
    )
    # Alas
    base_w = size * 0.16
    d.line(
        [cx - base_w, size * 0.86, cx + base_w, size * 0.86],
        fill=color,
        width=max(2, int(size * 0.05)),
    )
    return img


def ensure_mic_icon() -> str:
    """Pastikan file ikon mic ada; kembalikan path-nya."""
    path = os.path.join(_assets_dir(), "mic.png")
    if not os.path.exists(path):
        img = create_mic_icon()
        img.save(path)
    return path


if __name__ == "__main__":
    p = ensure_mic_icon()
    print(f"Ikon dibuat: {p}")
