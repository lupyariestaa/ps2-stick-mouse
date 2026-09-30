# Rencana Implementasi: Stick PS2 sebagai Mouse

> **Status dokumen:** ✅ **SELESAI (v1.0)** — semua FASE 0–3 tuntas & terverifikasi
> **Bahasa proyek:** Python
>
> 📎 **Dokumen terkait:** [`VOICE_TO_TEXT_PLAN.md`](./VOICE_TO_TEXT_PLAN.md) —
> rencana fitur baru **Voice-to-Text** (tombol Kotak & Segitiga).

---

## 1. Ringkasan Proyek

Membuat sebuah program yang mengubah **stik PlayStation 2** (yang terhubung ke laptop
lewat adaptor PS2 → USB) menjadi **mouse** untuk laptop.

Stik PS2 sudah dikonfirmasi **terbaca** oleh Windows dan muncul di
*Set up USB game controllers* dengan status **OK**, sehingga program cukup
membaca input dari perangkat HID yang sudah ada — tidak perlu menangani driver USB
di level rendah.

Program akan:
- Membaca input analog & tombol dari stik.
- Menerjemahkannya menjadi aksi mouse (gerak, klik, scroll).
- Menyediakan **mode toggle** agar stik tetap bisa dipakai main game normal.
- Punya **file konfigurasi** yang bisa diedit tanpa menyentuh kode.

---

## 2. Tujuan & Non-Tujuan

### 2.1 Tujuan (Goals)
- [ ] Stik PS2 bisa menggerakkan kursor mouse dengan mulus.
- [ ] Tombol stik bisa jadi klik kiri, klik kanan, dan scroll.
- [ ] Ada pengaturan *deadzone* dan *sensitivity* (kecepatan kursor).
- [ ] Ada tombol untuk **toggle mode** antara *mouse mode* dan *gamepad mode*.
- [ ] Semua pengaturan bisa diubah lewat file config (JSON).
- [ ] Program berjalan sebagai aplikasi konsol/background yang ringan.

### 2.2 Non-Tujuan (Non-Goals)
- Bukan untuk membuat driver USB custom (Windows sudah menangani stik).
- Bukan aplikasi dengan GUI penuh (cukup konsol + config file; GUI bisa jadi fase lanjutan).
- Tidak (untuk sekarang) mendukung macros/scripting lanjutan.

---

## 3. Kondisi Teknis Saat Ini (Hasil Pengecekan)

| Item | Status | Catatan |
|---|---|---|
| Stik PS2 + adaptor | ✅ Terbaca di Windows | Terlihat di `joy.cpl` dengan status OK |
| Workspace proyek | ✅ Ada | `C:\Lupy_Space\Company\stick-mouse` |
| Folder `docs/` | ✅ Dibuat | Berisi dokumen ini |
| **Python terinstall** | ✅ **SELESAI** | Python 3.12.10 (user-scope, via winget) |
| pip | ✅ Tersedia | pip 26.2.1 di dalam `.venv` |
| Virtual env `.venv` | ✅ Dibuat | Di root proyek |
| Dependensi (pygame, pynput, watchdog) | ✅ Terinstall | Lihat `requirements.txt` |
| Stik terbaca pygame | ✅ Terverifikasi | Lihat Bagian 3.1 |

**Path Python:** `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`
**Path venv:** `.venv\Scripts\python.exe`

### 3.1 Hasil Deteksi Stik (via pygame)

```
Jumlah joystick terdeteksi: 2
  [0] Twin USB Gamepad | axes=4 buttons=12 hats=1
  [1] Twin USB Gamepad | axes=4 buttons=12 hats=1
```

- Nama device: **Twin USB Gamepad** (adaptor PS2→USB 2-port, terdeteksi sebagai 2 joystick).
- Setiap device: **4 axis, 12 tombol, 1 hat (D-Pad)** — sesuai kebutuhan.
- **Keputusan:** program akan default memakai **joystick index 0**, dan index ini
  dibuat dapat dikonfigurasi (`joystick_index` di `config.json`).

> ℹ️ Karena ada 2 device, jika kamu ingin memakai stik pada port kedua, cukup ubah
> `joystick_index` menjadi `1` di config.

---

## 4. Arsitektur & Alur Program (Flow)

```
┌─────────────────────────────────────────────────────────────┐
│                        MAIN LOOP (polling)                    │
│                     ~ setara 100–250 Hz / frame               │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────┐
│  Baca input stik  │  ← pygame.joystick (axis + button + hat)
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  Cek mode aktif   │  ← variabel mode: MOUSE atau GAMEPAD
└──────────────────┘
        │
        ├─────────────► [GAMEPAD mode] ──► tidak sentuh mouse
        │                                    (biarkan OS/game pakai stik)
        ▼
   [MOUSE mode]
        │
        ▼
┌──────────────────┐
│  Terapkan         │  ← deadzone, kurva kecepatan (sensitivitas)
│  deadzone & curve │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  Aksi mouse       │  → move / click / scroll (pynput)
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  Frame pacing      │  ← sleep kecil agar CPU tidak 100%
└──────────────────┘
        │
        └──────────► loop lagi
```

### 4.1 Diagram Komponen

```
+-------------------+      +---------------------+      +--------------------+
|  Config Loader     |      |   Input Reader       |      |   Mouse Actuator    |
|  (config.json)     |----->|   (pygame.joystick)  |----->|   (pynput)          |
+-------------------+      +---------------------+      +--------------------+
        │                            │                            ▲
        │ pengaturan                 │ nilai axis/button          │ perintah
        ▼                            ▼                            │
+-------------------------------------------------------------------+
|                       MODE MANAGER / MAPPING ENGINE                 |
|   - deadzone  - sensitivity curve  - button mapping  - toggle mode |
+-------------------------------------------------------------------+
```

---

## 5. Pemetaan Kontrol (Default)

> Semua nilai di bawah akan **bisa diubah** lewat `config.json`.

| Input Stik PS2 | Index (adaptor ini) | Aksi Mouse (Mouse Mode) | Aksi (Gamepad Mode) | Status |
|---|---|---|---|---|
| Analog Kiri (X/Y) | axis 0/1 | Gerakkan kursor | diteruskan ke game | ✅ Aktif |
| Analog Kanan (X/Y) | axis 2/3 | Scroll (atas/bawah & kiri/kanan) | diteruskan ke game | ✅ Aktif |
| Tombol **✕ (Cross)** | **2** | Klik kiri | tombol game normal | ✅ Aktif |
| Tombol **◯ (Circle)** | **1** | Klik kanan | tombol game normal | ✅ Aktif |
| Tombol **□ (Square)** | **3** | *(dibebaskan / reserved)* | *(bebas)* | 🔒 **FREE** |
| Tombol **△ (Triangle)** | **0** | *(dibebaskan / reserved)* | *(bebas)* | 🔒 **FREE** |
| Tombol **L1** | **6** | Turunkan sensitivitas kursor | — | ✅ Aktif |
| Tombol **R1** | **7** | Naikkan sensitivitas kursor | — | ✅ Aktif |
| Tombol **Select** | **8** | Toggle Mouse/Gamepad | toggle juga | ✅ Aktif |
| Tombol **Start** | **9** | Keluar program | keluar juga | ✅ Aktif |

> **Terverifikasi via wizard** (`src/diagnose.py wizard`) pada adaptor "Twin USB Gamepad".
> **PENTING:** Adaptor ini **menukar X dan Segitiga** — Segitiga = index 0, X = index 2
> (berbeda dari urutan DualShock2 standar). Bila memakai adaptor lain, jalankan
> `wizard.bat` lagi untuk memetakan ulang.
>
> **Tombol FREE** (belum dipakai, untuk fitur besar mendatang): **Square (index 3)**
> dan **Triangle (index 0)**.

---

## 6. Perancangan Konfigurasi (`config.json`)

Contoh struktur awal (draft):

```json
{
  "joystick_index": 0,
  "deadzone": 0.15,
  "sensitivity": 12.0,
  "scroll_sensitivity": 1.0,
  "poll_interval_ms": 8,
  "toggle_button": 3,
  "invert_y": false,
  "button_map": {
    "left_click": 0,
    "right_click": 1,
    "middle_click": 2
  },
  "axis_map": {
    "cursor_x": 0,
    "cursor_y": 1,
    "scroll_x": 2,
    "scroll_y": 3
  }
}
```

---

## 7. Teknologi & Dependensi

| Kebutuhan | Pilihan | Alasan |
|---|---|---|
| Baca stik | `pygame` | Cross-platform, mudah, sudah terbukti baca joystick HID |
| Kontrol mouse | `pynput` | Kontrol mouse lintas platform, stabil |
| Config | `json` (built-in) | Tanpa dependensi tambahan |
| Watcher config | `watchdog` (opsional) | Reload config saat file diubah |

**File:** `requirements.txt` akan berisi: `pygame`, `pynput`, (opsional `watchdog`).

---

## 8. Rencana Struktur Folder (Target Akhir)

```
stick-mouse/
├── docs/
│   └── IMPLEMENTATION_PLAN.md      ← dokumen ini
├── src/
│   ├── __init__.py
│   ├── main.py                     ← entry point + main loop + reconnect
│   ├── config.py                   ← loader & validasi config
│   ├── config_watcher.py           ← hot-reload config (watchdog)
│   ├── joystick_input.py           ← wrapper pembacaan stik
│   ├── mouse_actuator.py           ← wrapper aksi mouse
│   ├── mapping.py                  ← deadzone/curve/scroll/sensitivitas
│   ├── mode_manager.py             ← pengelolaan mode mouse/gamepad
│   ├── controller.py               ← orkestrasi input -> aksi
│   ├── tray.py                     ← system tray icon (pystray)
│   └── diagnose.py                 ← alat diagnostik stik
├── config.json                     ← konfigurasi default
├── requirements.txt
├── README.md                       ← cara pakai
├── run.bat                         ← launcher utama
├── diagnose.bat                    ← launcher diagnostik
├── wizard.bat                      ← launcher wizard pemetaan tombol
├── build.bat / build.spec          ← build .exe
├── StickMouse.py                   ← entry untuk packaging
└── .gitignore
```

> Struktur ini dipakai sesuai keputusan pengguna (**multi-file rapi**).
> `controller.py`, `config_watcher.py`, `tray.py` ditambahkan di FASE 2–3.

### 8.1 Cara Menjalankan

```powershell
# Mode mouse (program utama)
.\.venv\Scripts\python.exe -u -m src.main
# atau klik run.bat

# Diagnostik stik (lihat axis & index tombol)
.\.venv\Scripts\python.exe -u -m src.diagnose
# atau klik diagnose.bat

# Build .exe
.\.venv\Scripts\pyinstaller build.spec --noconfirm
# atau klik build.bat  ->  dist\StickMouse\StickMouse.exe
```

> Dihentikan dengan **Ctrl+C**, tombol **Start**, atau menu tray **Keluar**.

---

## 9. Daftar Task (Implementation Tasks)

### FASE 0 — Persiapan Lingkungan ✅ SELESAI
- [x] **T0.1** Install Python 3.12.10 via `winget` (user-scope).
- [x] **T0.2** Verifikasi `python --version` & `pip --version` (berhasil).
- [x] **T0.3** Buat virtual environment (`.venv`) di root proyek.
- [x] **T0.4** Install dependensi: `pygame`, `pynput`, `watchdog`.
- [x] **T0.5** Buat `requirements.txt` & `.gitignore`.
- [x] **T0.6** Verifikasi stik terbaca pygame (2 device "Twin USB Gamepad").

### FASE 1 — MVP (Minimum Viable Product) ✅ SELESAI
- [x] **T1.1** Skrip deteksi stik: `src/diagnose.py::show_devices` + `list_joysticks()`.
- [x] **T1.2** Skrip diagnostik real-time: `src/diagnose.py::monitor` (nilai axis & index tombol).
- [x] **T1.3** Gerakkan kursor dengan analog kiri (`src/main.py` + `AxisMapper`).
- [x] **T1.4** Deadzone (`src/mapping.py::apply_deadzone`) — nilai kecil dimatikan & di-scale ulang.
- [x] **T1.5** Sensitivity/curve (`apply_curve` + smoothing EMA di `AxisMapper`).
- [x] **T1.6** Mapping tombol → klik (fungsi `press/release/click` siap di `MouseActuator`;
      integrasi edge-triggered ke main loop diselesaikan di FASE 2 Task T2.2, lihat catatan).

> **Catatan T1.6:** `MouseActuator` sudah menyediakan `press()`, `release()`, `click()`,
> dan `release_all()`. Integrasi penuh (klik saat tombol ditekan/dilepas) digabung
> bersama Mode Manager di FASE 2 agar tidak ada klik liar saat ganti mode.
> Verifikasi MVP FASE 1 difokuskan pada pergerakan kursor + deteksi input.

### FASE 2 — Fitur Lengkap ✅ SELESAI
- [x] **T2.1** Scroll via analog kanan (`AxisMapper.scroll_delta` + `ScrollAccumulator`).
- [x] **T2.2** Mode Manager: toggle Mouse ↔ Gamepad (tombol **Triangle**, index 3).
- [x] **T2.3** Loader `config.json` + validasi nilai (sudah ada sejak FASE 0/1, diperkuat).
- [x] **T2.4** Hot-reload config pakai `watchdog` (`src/config_watcher.py`).
- [x] **T2.5** Handle stik dicabut/colok ulang tanpa crash (retry reconnect di `main.py`).
- [x] **T2.6** Indikator status di konsol (banner + log `[MODE]`, `[CONFIG]`, `[WARN]`).

> **Catatan:** Klik kiri/kanan/tengah kini terintegrasi penuh (edge-triggered) di
> `controller.py`, sehingga T1.6 (yang ditunda) tuntas di sini.

### FASE 3 — Polishing & Dokumentasi ✅ SELESAI
- [x] **T3.1** Tangani error ramah: `load_config(strict=False)` fallback ke default saat config rusak;
      error stik tidak ada / terputus sudah ditangani sejak FASE 2.
- [x] **T3.2** `README.md` lengkap (instalasi, cara pakai, konfigurasi, troubleshooting).
- [x] **T3.3** Launcher: `run.bat` & `diagnose.bat`.
- [x] **T3.4** Tray icon (`src/tray.py` via `pystray` + `Pillow`): ganti mode & keluar.
- [x] **T3.5** Packaging `.exe` (`build.spec` + `build.bat` + `StickMouse.py`).

### FASE 3 — Fitur Tambahan (Permintaan Pengguna) ✅ SELESAI
- [x] **F3.1** Tombol **Select** → toggle Mouse/Gamepad (dipindah dari Triangle).
- [x] **F3.2** Tombol **Start** → keluar program.
- [x] **F3.3** Tombol **L1/R1** → turunkan/naikkan sensitivitas kursor (real-time, clamped).
- [x] **F3.4** Tombol **Square & Triangle** dibebaskan (reserved) untuk fitur mendatang.
- [x] **F3.5** Klik tengah dinonaktifkan (`middle_click: -1`) karena Square dibebaskan.

> **Catatan penting:** Index default tombol Select/Start/L1/R1 (`8/9/6/7`) adalah
> **tebakan umum** dan **WAJIB diverifikasi** dengan `diagnose.bat` pada adaptor
> "Twin USB Gamepad". Bila tombol salah fungsi, sesuaikan `control_buttons`
> di `config.json`.

---

## 10. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi | Status |
|---|---|---|---|
| Python belum terinstall | Blocker total | FASE 0 wajib lebih dulu | ✅ Teratasi |
| Index tombol berbeda dari ekspektasi | Tombol salah fungsi | Mode diagnostik (T1.2) + `config.json` | ✅ Tersedia |
| Kursor *drift* saat stik diam | Ganggu pemakaian | Deadzone (T1.4) + kurva halus | ✅ Teratasi |
| Polling terlalu cepat → CPU tinggi | Laptop panas/berat | `poll_interval_ms` + frame pacing | ✅ Teratasi |
| Stik dicabut saat program jalan | Crash | Try/except + reconnect (T2.5) | ✅ Teratasi |
| Konflik dengan game (anti-cheat) | Game menolak program | Sediakan mode Gamepad agar bisa dimatikan | ✅ Toggle Triangle |
| Input "nyangkut" (tombol tetap tertekan) | Klik terus-menerus | Lepas semua tombol saat ganti mode / stik hilang | ✅ Teratasi |

---

## 11. Definisi Selesai (Definition of Done)

Sebuah task dianggap selesai jika:
1. Kode berjalan tanpa error di laptop target.
2. Perilaku sesuai deskripsi task.
3. Diuji langsung dengan stik **dan** dengan nilai config default.
4. Perubahan dijelaskan singkat ke pengguna.

Proyek dianggap selesai (versi 1.0) jika:
- Semua task FASE 0–2 selesai.
- Kursor, klik, scroll berfungsi dan nyaman.
- Toggle mode berfungsi.
- Config bisa diubah & berlaku.

---

## 12. Keputusan Pengguna (SUDAH DIJAWAB)

| # | Pertanyaan | Keputusan |
|---|---|---|
| 1 | Struktur kode | **Multi-file rapi** (`src/` dengan modul terpisah) |
| 2 | Tombol toggle mode | **Triangle** |
| 3 | Scroll | **Analog kanan** |
| 4 | Hot-reload config | **Bebas** (diimplementasikan bila memungkinkan) |
| 5 | Peran stik | Saat program jalan, stik **khusus Mouse Mode** |
| 6 | Fitur tambahan | **Bebas** — tambahkan sesuai pertimbangan developer |

### 12.1 Implikasi Keputusan

- **#1** → Struktur folder di Bagian 8 dipakai apa adanya (bukan MVP satu file).
- **#2** → `toggle_button` default = index tombol Triangle (diverifikasi di Fase 1).
- **#3** → `scroll_x` = axis 2, `scroll_y` = axis 3 (analog kanan). Diverifikasi runtime.
- **#5** → Mode default saat start = **Mouse Mode**. Gamepad mode tetap disediakan
  sebagai fitur toggle (bisa dinyalakan manual jika sewaktu-waktu dibutuhkan).
- **#6** → Fitur tambahan yang akan dipertimbangkan (lihat Bagian 12.2).

### 12.2 Fitur Tambahan yang Diusulkan Developer

- [ ] **Double-click** (tombol khusus atau trigger)
- [ ] **Drag & drop** (tahan tombol lalu gerakkan kursor)
- [ ] **Smoothing / akselerasi kursor** agar gerakan lebih halus
- [ ] **Modifier scroll cepat** (mis. tombol R1 = scroll lebih cepat)
- [ ] **Auto-disable** saat kursor tidak dibutuhkan
- [ ] **Notifikasi suara/console** saat ganti mode

> Semua fitur di atas bersifat opsional dan akan dikerjakan pada FASE 3.

---

## 13. Riwayat Perubahan

| Tanggal | Versi | Catatan |
|---|---|---|
| — | 0.1 | Draft awal dibuat, menunggu review pengguna |
| — | 0.2 | Keputusan pengguna dicatat (Bagian 12). FASE 0 (lingkungan) selesai: Python 3.12.10 + deps terinstall, stik terverifikasi terbaca pygame. |
| — | 0.3 | FASE 1 (MVP) selesai: struktur `src/` multi-file, pergerakan kursor, deadzone, curve/smoothing, diagnostik. Semua modul lolos `py_compile` + unit test logika + smoke test `main.py`. |
| — | 0.4 | FASE 2 selesai: scroll analog kanan, toggle mode (Triangle), integrasi klik penuh, hot-reload config (watchdog), reconnect stik, indikator status. Semua diverifikasi dengan unit test (mock) + test hot-reload + smoke test. |
| — | 0.5 | FASE 3 selesai: error handling ramah, README, launcher `.bat`, tray icon, packaging `.exe`. Fitur tambahan: Select=toggle, Start=quit, L1/R1=sensitivitas, Square/Triangle reserved. Semua diverifikasi (unit test mock + smoke test main + .exe). **Proyek mencapai v1.0.** |
| — | 0.6 | Verifikasi pemetaan tombol via wizard: ditemukan adaptor **menukar X & Segitiga** (Segitiga=0, X=2). `config.json` diperbaiki (X→klik kiri, Bulat→klik kanan). Ditambahkan `wizard.bat` + mode wizard di `diagnose.py`. Tombol **FREE: Square (3) & Triangle (0)**. |

---

> **CATATAN:** Dokumen ini adalah rencana. **Tidak ada kode yang akan dieksekusi
> atau ditulis sampai pengguna menyetujui** dan menjawab pertanyaan di Bagian 12.
