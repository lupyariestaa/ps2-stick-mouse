# 🎮 PS2 Stick Mouse

> **Ubah stik PlayStation 2 jadi mouse + input suara buat laptop kamu.** 🖱️🎤

Gerakkan kursor, klik, scroll, atur sensitivitas, sampai **ngetik pakai suara**
(voice-to-text) — semuanya cuma dari stik PS2 yang dicolok lewat adaptor USB.
Bisa dipakai buat main, ngoding santai di sofa, atau sekadar eksperimen seru.

<p align="left">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white">
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg">
  <img alt="Status" src="https://img.shields.io/badge/status-active-brightgreen">
</p>

---

## ✨ Fitur

| Fitur | Keterangan |
|---|---|
| 🖱️ **Gerak kursor** | Analog **kiri** menggerakkan pointer |
| 📜 **Scroll** | Analog **kanan** untuk scroll (atas/bawah & kiri/kanan) |
| 🖱️ **Klik** | **X (✕)** = klik kiri, **Bulat (◯)** = klik kanan |
| 🎤 **Voice-to-text** | **Kotak (□)** = mulai/stop rekam → teks diketik otomatis ke aplikasi aktif |
| ⏎ **Enter** | **Segitiga (△)** = tekan Enter |
| 🔀 **Mode ganda** | Tombol **Select** men-toggle antara *Mouse* & *Gamepad* |
| ⚙️ **Atur sensitivitas** | **L1** = turunkan, **R1** = naikkan (real-time) |
| 🛑 **Keluar** | Tombol **Start** menutup program |
| 🎛️ **System tray** | Ikon di tray untuk ganti mode & keluar |
| 🔄 **Hot-reload config** | Edit `config.json` → langsung berlaku tanpa restart |
| 🔌 **Auto-reconnect** | Cabut/colok ulang stik tanpa crash |
| 🔊 **Auto-boost mic** | Volume mikrofon dinaikkan otomatis saat startup |
| 🪄 **Wizard pemetaan** | Petakan ulang tombol adaptor apa pun otomatis |

---

## 🎤 Demo Voice-to-Text

```
Tekan Kotak (□)  →  ikon mic muncul + bunyi bip  →  bicara
    →  tekan Kotak lagi  →  teks otomatis diketik
    →  (tekan Segitiga) = Enter
```

Contoh: kamu buka YouTube, tekan Kotak, bilang *"lagu lofi hip hop"*, tekan Kotak
lagi, lalu tekan Segitiga → langsung ter-search! Tanpa sentuh keyboard. 😎

> Selama merekam, **kursor mouse dibekukan** biar tidak salah gerak
> (bisa dimatikan di `config.json`).

---

## 📋 Daftar Isi

- [Persyaratan](#-persyaratan)
- [Instalasi](#-instalasi)
- [Cara Pakai](#-cara-pakai)
- [Peta Tombol](#-peta-tombol-default)
- [Konfigurasi](#️-konfigurasi-configjson)
- [Diagnostik & Wizard](#-diagnostik--wizard)
- [Build .exe](#-build-exe)
- [Struktur Proyek](#-struktur-proyek)
- [Troubleshooting](#-troubleshooting)
- [Kontribusi](#-kontribusi)
- [Lisensi](#-lisensi)

---

## 📦 Persyaratan

- **Windows 10/11**
- **Python 3.11+** (diuji di 3.12.10)
- **Adaptor PS2 → USB** + stik PS2 (yang sudah terbaca Windows)
- **Mikrofon** (untuk fitur voice)
- **Koneksi internet** (untuk voice Google Speech; ada opsi offline)

> Cek apakah stik terbaca: buka **Run** → ketik `joy.cpl` → lihat *Set up USB game controllers*.

---

## 🚀 Instalasi

### Opsi A — Langsung pakai `.exe` (paling gampang)

1. Download/masuk ke folder `dist/StickMouse/`
2. Klik dua kali **`StickMouse.exe`**
3. File `config.json` akan dibuat otomatis di folder yang sama
4. Selesai! 🎉

### Opsi B — Dari source (untuk ngoding)

```powershell
# 1) Clone repo
git clone https://github.com/lupyariestaa/ps2-stick-mouse.git
cd ps2-stick-mouse

# 2) Buat virtual environment
python -m venv .venv

# 3) Install dependensi
.\.venv\Scripts\pip install -r requirements.txt

# 4) Jalankan
.\.venv\Scripts\python.exe -u -m src.main
```

Atau cukup **klik dua kali `run.bat`**. 👍

---

## 🎮 Cara Pakai

```powershell
# Jalankan program utama
run.bat
# atau: .\.venv\Scripts\python.exe -u -m src.main
```

**Keluar dari program:** tekan tombol **Start**, atau **Ctrl+C** di terminal, atau
klik kanan ikon **tray** → Keluar.

---

## 🕹️ Peta Tombol (Default)

| Tombol fisik | Index | Fungsi |
|---|---|---|
| △ Segitiga | 0 | ⏎ Enter |
| ◯ Bulat | 1 | 🖱️ Klik kanan |
| ✕ X | 2 | 🖱️ Klik kiri |
| □ Kotak | 3 | 🎤 Voice-to-text (mulai/stop) |
| L1 | 6 | ⚙️ Sensitivitas turun |
| R1 | 7 | ⚙️ Sensitivitas naik |
| Select | 8 | 🔀 Ganti mode (Mouse/Gamepad) |
| Start | 9 | 🛑 Keluar |

> ⚠️ **Index tombol bergantung pada adaptor!** Contoh di atas untuk adaptor
> "Twin USB Gamepad" — yang kebetulan **menukar X dan Segitiga**
> (Segitiga = 0, X = 2). Kalau adaptormu beda, jalankan **`wizard.bat`** untuk
> memetakan ulang secara otomatis.

---

## ⚙️ Konfigurasi (`config.json`)

Semua pengaturan ada di `config.json` dan berlaku otomatis (hot-reload — edit
file, langsung berubah tanpa restart).

```json
{
  "joystick_index": 0,
  "deadzone": 0.15,
  "sensitivity": 12.0,
  "scroll_sensitivity": 1.0,
  "poll_interval_ms": 8,
  "invert_y": false,
  "smoothing": 0.0,
  "sensitivity_step": 1.0,
  "sensitivity_min": 2.0,
  "sensitivity_max": 40.0,
  "startup_grace_seconds": 2.0,
  "control_buttons": {
    "toggle_mode": 8,
    "quit": 9,
    "sens_up": 7,
    "sens_down": 6
  },
  "reserved_buttons": [],
  "voice": {
    "enabled": true,
    "language": "id-ID",
    "toggle_button": 3,
    "enter_button": 0,
    "enter_hold_seconds": 0.0,
    "freeze_mouse_while_recording": true,
    "auto_enter": false,
    "recognizer": "google",
    "typing_interval": 0.01,
    "overlay_enabled": true,
    "beep_enabled": true,
    "auto_boost_mic": true
  },
  "button_map": {
    "left_click": 2,
    "right_click": 1,
    "middle_click": -1
  },
  "axis_map": {
    "cursor_x": 0,
    "cursor_y": 1,
    "scroll_x": 2,
    "scroll_y": 3
  }
}
```

<details>
<summary><b>Penjelasan umum</b></summary>

| Field | Arti |
|---|---|
| `joystick_index` | Stik mana yang dipakai (0/1) |
| `deadzone` | Area mati di tengah analog (naikkan bila kursor *drift*) |
| `sensitivity` | Kecepatan kursor |
| `scroll_sensitivity` | Kecepatan scroll |
| `poll_interval_ms` | Jeda antar frame (kecil = responsif) |
| `invert_y` | Balik arah vertikal kursor |
| `smoothing` | Kehalusan gerakan (0.0 = tanpa smoothing) |
| `startup_grace_seconds` | Abaikan tombol sekian detik saat startup |
| `control_buttons` | Index tombol kontrol |
| `button_map` | Index tombol klik (`-1` = nonaktif) |
| `axis_map` | Index axis kursor & scroll |

</details>

<details>
<summary><b>Penjelasan voice-to-text</b></summary>

| Field | Arti |
|---|---|
| `enabled` | Aktifkan/matikan fitur voice |
| `language` | Kode bahasa (`id-ID`, `en-US`, dll) |
| `toggle_button` | Index tombol mulai/stop rekam |
| `enter_button` | Index tombol Enter |
| `enter_hold_seconds` | Lama tahan Enter (0 = langsung klik) |
| `freeze_mouse_while_recording` | Bekukan mouse saat merekam |
| `auto_enter` | Otomatis Enter setelah mengetik |
| `recognizer` | `google` (online) atau `sphinx` (offline) |
| `typing_interval` | Jeda antar karakter saat mengetik |
| `overlay_enabled` | Tampilkan overlay ikon mic |
| `beep_enabled` | Bunyi bip saat mulai/berhenti |
| `auto_boost_mic` | Naikkan volume mic otomatis saat startup |

</details>

---

## 🔍 Diagnostik & Wizard

**Wizard pemetaan tombol** (memandu kamu menekan tombol lalu mengisi config otomatis):

```powershell
wizard.bat
```

**Monitor real-time** (lihat nilai axis & index tombol):

```powershell
diagnose.bat
```

Tekan tombol di stik, program akan mencetak `[BUTTON] index N DITEKAN`.

---

## 📦 Build `.exe`

```powershell
# Klik dua kali build.bat, atau:
.\.venv\Scripts\pyinstaller build.spec --noconfirm
```

Hasil ada di `dist\StickMouse\StickMouse.exe`.

---

## 📂 Struktur Proyek

```
ps2-stick-mouse/
├── src/
│   ├── main.py              ← entry point + main loop + reconnect
│   ├── config.py            ← loader & validasi config
│   ├── config_watcher.py    ← hot-reload config (watchdog)
│   ├── controller.py        ← orkestrasi input -> aksi
│   ├── joystick_input.py    ← pembacaan stik (pygame)
│   ├── mouse_actuator.py    ← kontrol mouse (pynput)
│   ├── mapping.py           ← deadzone, curve, scroll, sensitivitas
│   ├── mode_manager.py      ← mode mouse/gamepad
│   ├── tray.py              ← system tray icon (pystray)
│   ├── diagnose.py          ← diagnostik + wizard pemetaan
│   └── voice/               ← fitur voice-to-text
│       ├── recorder.py      ← rekam audio (pyaudio)
│       ├── recognizer.py    ← Google Speech / sphinx
│       ├── typer.py         ← ketik teks (pynput)
│       ├── beeper.py        ← feedback bip
│       ├── mic_boost.py     ← auto-boost volume mic
│       ├── icon.py          ← generator ikon mic
│       ├── overlay.py       ← overlay ikon mic (tkinter)
│       └── voice_manager.py ← state machine
├── assets/                  ← ikon overlay (bisa diganti)
├── docs/                    ← dokumentasi perencanaan
├── config.json
├── requirements.txt
├── run.bat / diagnose.bat / wizard.bat / build.bat
└── StickMouse.py
```

---

## 🛠️ Teknologi

| Bagian | Library |
|---|---|
| Baca stik | [`pygame`](https://www.pygame.org/) |
| Kontrol mouse & keyboard | [`pynput`](https://pynput.readthedocs.io/) |
| Voice-to-Text | [`SpeechRecognition`](https://pypi.org/project/SpeechRecognition/) + Google Web Speech |
| Rekam audio | [`pyaudio`](https://pypi.org/project/PyAudio/) |
| System tray | [`pystray`](https://pypi.org/project/pystray/) + [`Pillow`](https://pillow.readthedocs.io/) |
| Hot-reload | [`watchdog`](https://pypi.org/project/watchdog/) |
| Kontrol volume mic | [`pycaw`](https://pypi.org/project/pycaw/) |

---

## 🔧 Troubleshooting

| Masalah | Solusi |
|---|---|
| Stik tidak terdeteksi | Cek `joy.cpl`; coba `joystick_index` 0 atau 1 |
| Tombol salah fungsi | Jalankan `wizard.bat` |
| Kursor *drift* saat diam | Naikkan `deadzone` |
| Kursor terlalu cepat/lambat | Ubah `sensitivity`, atau pakai L1/R1 |
| Game anti-cheat menolak | Tekan Select → mode Gamepad, atau tutup program |
| Voice tidak dikenali | Cek volume mic (auto-boost; bisa atur manual di Settings → Sound → Input) |
| Voice tidak jalan (offline) | Google Speech butuh internet |
| Voice salah bahasa | Ubah `language` (mis. `en-US`) |
| Program keluar sendiri saat start | Naikkan `startup_grace_seconds` |
| Ingin ganti ikon mic | Ganti file `assets/mic.png` (lihat `assets/README.md`) |

---

## 🤝 Kontribusi

Kontribusi, issue, dan ide fitur sangat diterima!

1. Fork repo ini
2. Buat branch baru (`git checkout -b fitur-keren`)
3. Commit perubahan (`git commit -m 'Tambah fitur keren'`)
4. Push (`git push origin fitur-keren`)
5. Buka Pull Request

---

## 📄 Lisensi

Proyek ini dirilis di bawah **[MIT License](LICENSE)** — bebas dipakai, diubah,
dan dibagikan.

---

<p align="center">
  Dibuat dengan ❤️ dan sedikit 🎮 + 🎤
</p>
