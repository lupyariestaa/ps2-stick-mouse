# Assets - Ikon Mic (Overlay Voice-to-Text)

Folder ini berisi ikon yang dipakai overlay saat merekam suara.

## Ikon Default

`mic.png` — dibuat otomatis oleh program (`src/voice/icon.py`) jika belum ada.
Ikon default: kapsul mikrofon merah dengan bracket.

## Cara Mengganti Ikon

1. Siapkan gambar ikon kamu (format **PNG**, latar belakang transparan lebih bagus).
2. Ukuran ideal: **96x96 piksel** atau **128x128 piksel** (akan di-resize otomatis
   ke 72px saat ditampilkan, tapi gambar yang lebih besar terlihat lebih tajam).
3. Ganti file `assets/mic.png` dengan gambar milikmu (nama file harus `mic.png`).
4. Jalankan ulang program.

> **Catatan:** Program **tidak** memakai SVG. Library tampilan (tkinter) tidak
> bisa merender SVG secara langsung. Jadi gunakan PNG.
>
> Kalau kamu punya gambar berformat SVG/ICO/JPG, konversi dulu ke PNG pakai
> tool online (misal cloudconvert.com) atau Photoshop/Inkscape.

## Kalau Ingin Generate Ulang Ikon Default

Hapus `assets/mic.png`, lalu jalankan:

```powershell
.\.venv\Scripts\python.exe -m src.voice.icon
```

## Kustomisasi Lanjutan (via Kode)

Kalau kamu mau mengubah bentuk ikon lewat kode, edit fungsi `create_mic_icon()`
di `src/voice/icon.py`. Parameter yang tersedia:
- `size` — ukuran gambar (default 96)
- `color` — warna RGB, mis. `(220, 60, 60)` untuk merah

Contoh mengubah warna jadi biru:

```python
img = create_mic_icon(size=128, color=(60, 120, 220))
img.save("assets/mic.png")
```
