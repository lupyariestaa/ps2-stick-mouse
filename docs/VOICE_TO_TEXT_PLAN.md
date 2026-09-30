# Rencana Implementasi: Fitur Voice-to-Text (Tombol Kotak)

> **Status dokumen:** ✅ V0–V2 SELESAI & terverifikasi — lanjut V3 (robustness)
> **Modul terkait:** `stick-mouse` (proyek utama)
> **Tombol:** Kotak (index 3) & Segitiga (index 0)

---

## 0.1 Ringkasan Verifikasi

| Test | Hasil |
|---|---|
| Mikrofon merekam + volume | ✅ (boost 3% → 100%) |
| Google Speech Bahasa Indonesia | ✅ `'tapi sekarang enak hampir maksimal'` |
| Freeze mouse saat merekam (mock) | ✅ |
| Tombol Kotak toggle & Segitiga hold-enter (mock) | ✅ |
| End-to-end rekam → STT → teks | ✅ `'this is'` |
| `main.py` dengan voice + auto-boost + overlay | ✅ berjalan bersih |
| `config.json` voice section | ✅ |

---

## 0. Hasil Verifikasi FASE V0 (PENTING!)

✅ **Semua verifikasi LULUS:**
- Mikrofon laptop berfungsi (Realtek Audio).
- `SpeechRecognition`, `pyaudio`, `pycaw`, `comtypes` terinstall.
- Google Speech **berhasil mengenali Bahasa Indonesia**:
  > Input suara → hasil: `'tapi sekarang enak hampir maksimal'`

⚠️ **TEMUAN PENTING:** Volume mikrofon awalnya **sangat pelan (~3%)**, sehingga
STT gagal. Setelah dinaikkan ke 100% (via `pycaw`), akurasi menjadi sempurna.

**Implikasi:** Program **harus** menyertakan langkah *auto-boost volume mic* saat
startup (atau minimal memperingatkan pengguna bila level terlalu rendah).
Fitur ini akan jadi bagian dari FASE V1/V2.

**Device mikrofon terdeteksi:**
```
[1] Microphone (Realtek(R) Audio)
[5] Microphone (Realtek(R) Audio)
[10] Microphone (Realtek HD Audio Mic input)
```

---

## 1. Ringkasan Fitur

Menambahkan kemampuan **voice-to-text** (bicara → jadi teks) ke dalam program
stick-mouse, dikendalikan dari tombol stik PS2.

**Alur yang diinginkan pengguna:**

```
1. User klik tombol KOTAK (index 3)
      ↓
2. Ikon "mic" muncul di dekat kursor (mulai merekam)
      ↓
3. User bicara: "Tolong kirim email ke bos"
      ↓
4. User klik tombol KOTAK lagi
      ↓
5. Rekaman berhenti → dikirim ke Google Speech
      ↓
6. Teks hasil diketik otomatis: "Tolong kirim email ke bos"
      ↓
7. (Opsional) User klik SEGITIGA (index 0) untuk tekan Enter
```

Tujuan akhir: pengguna bisa **input teks tanpa menyentuh keyboard** sama sekali.

---

## 2. Keputusan Pengguna (SUDAH DIJAWAB)

| # | Aspek | Keputusan |
|---|---|---|
| 1 | Engine STT | **Google Speech API** (online, gratis) |
| 2 | Bahasa | **Bisa dikonfigurasi** (default `id-ID`) |
| 3 | Output teks | **Ketik otomatis** (typing simulation) |
| 4 | Feedback visual | **Overlay ikon mic** di dekat kursor |
| 5 | Pola tombol | **Toggle** — Kotak (3) mulai & berhenti |
| 6 | Mouse saat rekam | **Di-freeze** (kursor & klik nonaktif) |
| 7 | Auto-Enter | **Tidak** (manual via Segitiga) |
| 8 | Tombol Enter | **Segitiga (index 0)** = tekan Enter |
| 9 | Batas waktu rekam | **Tanpa batas** |
| 10 | Lokasi dokumen | File terpisah (dokumen ini) |

---

## 3. Apakah Fitur Ini Bisa Dibangun?

✅ **BISA.** Hasil pengecekan lingkungan:

| Item | Status | Catatan |
|---|---|---|
| Koneksi internet | ✅ Ada | Untuk Google Speech API |
| `speech_recognition` | ❌ Belum | Akan diinstall |
| `pyaudio` | ❌ Belum | Untuk menangkap audio mikrofon |
| Mikrofon | ❓ Perlu dicek | Asumsi laptop punya mikrofon |
| Windows SAPI | ✅ Tersedia | Cadangan (offline) bila internet mati |

> **BLOCKER potensial:** Mikrofon. Perlu dipastikan laptop bisa merekam audio
> dari mikrofon. Akan diverifikasi di TASK-0.

---

## 4. Teknologi yang Dipakai

| Kebutuhan | Teknologi | Alasan |
|---|---|---|
| Tangkap audio | `pyaudio` | Standar untuk `speech_recognition` di Windows |
| Speech-to-Text | `SpeechRecognition` + Google Web API | Gratis, akurasi baik, support `id-ID` |
| Ketik teks | `pynput.keyboard` | Sudah dipakai di proyek (konsisten) |
| Overlay ikon | `tkinter` (bawaan Python) | Ringan, tanpa dependensi tambahan |
| Cadangan offline | `SpeechRecognition` + `recognize_sphinx` / SAPI | Bila internet mati |

### 4.1 Cara Kerja Google Speech (bukan AI generatif)
Google Web Speech API adalah layanan **speech recognition** klasik (bukan LLM).
Kita kirim file audio → Google mengembalikan teks. Gratis dan tanpa API key
untuk pemakaian ringan (ada batas wajar).

---

## 5. Arsitektur & Alur Teknis

```
┌──────────────────────────────────────────────────────────────┐
│                    MAIN LOOP (src/main.py)                     │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────┐    tombol Kotak ditekan
│  Controller.update()  │────────────────────────┐
└──────────────────────┘                          ▼
        │                              ┌──────────────────────┐
        │ (mode mouse)                 │  VoiceManager         │
        ▼                              │  .toggle()            │
┌──────────────────────┐              └──────────────────────┘
│  UpdateMouse / Freeze │                        │
└──────────────────────┘                        ├── START → mulai rekam
                                                 │           tampil overlay
                                                 │
                                                 └── STOP  → proses STT
                                                             ketik teks
                                                             sembunyikan overlay
```

### 5.1 Modul Baru (✅ sudah dibuat)

```
src/voice/
├── __init__.py
├── recorder.py        ✅ rekam audio (pyaudio, thread)
├── recognizer.py      ✅ Google Speech / sphinx wrapper
├── typer.py           ✅ ketik teks (pynput)
├── beeper.py          ✅ feedback bip (winsound)
├── mic_boost.py       ✅ auto-boost volume mic (pycaw)
├── icon.py            ✅ generator ikon mic (Pillow)
├── overlay.py         ✅ overlay tkinter transparan
└── voice_manager.py   ✅ state machine (IDLE/RECORDING/PROCESSING)
```

### 5.2 State Machine VoiceManager

```
   ┌─────────┐   tekan Kotak    ┌───────────┐
   │  IDLE   │ ───────────────► │ RECORDING │
   └─────────┘                  └───────────┘
        ▲                            │ tekan Kotak
        │                            ▼
        │                     ┌───────────────┐
        │◄────────────────────│ PROCESSING    │
        │   selesai/AKHIR     │ (STT + ketik) │
        │                     └───────────────┘
        │
   (kembali ke IDLE, overlay hilang)
```

- **IDLE:** tidak merekam, mouse aktif normal.
- **RECORDING:** merekam audio, overlay mic tampil, mouse di-freeze.
- **PROCESSING:** audio dikirim ke Google, teks diketik, mouse tetap freeze.
- Setelah selesai → kembali ke **IDLE**.

---

## 6. Pemetaan Tombol

| Tombol | Index | Fungsi | Status |
|---|---|---|---|
| **Kotak (□)** | 3 | Toggle rekam (mulai/berhenti) | 🎤 Baru |
| **Segitiga (△)** | 0 | Tekan Enter | ⏎ Baru |
| X (✕) | 2 | Klik kiri | (tetap) |
| Bulat (◯) | 1 | Klik kanan | (tetap) |
| L1 / R1 | 6 / 7 | Sensitivitas | (tetap) |
| Select | 8 | Ganti mode | (tetap) |
| Start | 9 | Keluar | (tetap) |

> Tombol **Segitiga (0)** yang tadinya free kini dipakai untuk Enter.
> Tombol **Kotak (3)** dipakai untuk voice-to-text.
> **Tidak ada tombol free tersisa** (Kotak & Segitiga terpakai).

---

## 7. Penambahan Konfigurasi (`config.json`)

```json
{
  "voice": {
    "enabled": true,
    "language": "id-ID",
    "toggle_button": 3,
    "enter_button": 0,
    "freeze_mouse_while_recording": true,
    "auto_enter": false,
    "recognizer": "google",
    "timeout_seconds": 0,
    "typing_interval": 0.01,
    "overlay_enabled": true
  }
}
```

| Field | Arti |
|---|---|
| `enabled` | Aktifkan/matikan fitur voice |
| `language` | Kode bahasa (`id-ID`, `en-US`, dll) |
| `toggle_button` | Index tombol mulai/stop rekam (default 3) |
| `enter_button` | Index tombol Enter (default 0) |
| `freeze_mouse_while_recording` | Bekukan mouse saat merekam |
| `auto_enter` | Otomatis Enter setelah mengetik (default off) |
| `recognizer` | `google` (online) atau `sphinx` (offline) |
| `timeout_seconds` | 0 = tanpa batas |
| `typing_interval` | Jeda antar karakter saat mengetik |
| `overlay_enabled` | Tampilkan overlay ikon mic |

---

## 8. Daftar Task (Implementation Tasks)

### FASE V0 — Persiapan & Verifikasi ✅ SELESAI
- [x] **V0.1** Verifikasi mikrofon merekam (Realtek Audio, OK).
- [x] **V0.2** Install `SpeechRecognition`, `pyaudio`, `pycaw`, `comtypes`.
- [x] **V0.3** Uji tangkap audio (rekam WAV, OK).
- [x] **V0.4** Uji kirim ke Google Speech → **berhasil (Bahasa Indonesia)**.
- [x] **V0.5** Update `requirements.txt`.
- [x] **V0.6** *(temuan)* Perbaiki volume mic pelan → boost ke 100% via `pycaw`.

### FASE V1 — MVP Voice-to-Text ✅ SELESAI
- [x] **V1.1** `voice/recorder.py` — rekam audio (thread terpisah, start/stop manual).
- [x] **V1.2** `voice/recognizer.py` — wrapper Google Speech (+ fallback sphinx).
- [x] **V1.3** `voice/typer.py` — ketik teks via `pynput.keyboard`.
- [x] **V1.4** `voice/voice_manager.py` — state machine (IDLE/RECORDING/PROCESSING).
- [x] **V1.5** Integrasi tombol **Kotak (3)** ke `Controller` (toggle rekam).
- [x] **V1.6** Freeze mouse saat RECORDING/PROCESSING (terverifikasi via mock test).
- [x] **V1.7** Tombol **Segitiga (0)** = tekan Enter (hold-to-enter).
- [x] **V1.8** Section `voice` di `config.json` + `config.py` (+ `VoiceConfig` dataclass).
- [x] **V1.9** `voice/mic_boost.py` — auto-boost volume mic (temuan V0).

### FASE V2 — Overlay & UX ✅ SELESAI
- [x] **V2.1** `voice/overlay.py` — jendela transparan tkinter (topmost, tanpa border).
- [x] **V2.2** Tampil saat RECORDING, sembunyi saat selesai (via callback state).
- [x] **V2.3** Overlay di thread terpisah (aman dari main loop).
- [x] **V2.4** `voice/icon.py` — generate ikon mic PNG otomatis (+ `assets/README.md`).
- [x] **V2.5** Log status di console (`[VOICE] Merekam...`, `[VOICE] Hasil: ...`).
- [x] **V2.6** `voice/beeper.py` — feedback suara (bip mulai/stop/error).

### FASE V3 — Robustness & Polishing ✅ SELESAI
- [x] **V3.1** Tangani error: mikrofon gagal, tidak ada suara terdeteksi (`NoSpeechError`).
- [x] **V3.2** Tangani error jaringan (`NetworkError`) → notif + beep error.
- [x] **V3.3** Cegah spam tombol: toggle diabaikan saat PROCESSING.
- [x] **V3.4** Voice nonaktif di Gamepad mode (terverifikasi via mock test).
- [x] **V3.5** Update `README.md` & dokumentasi.
- [ ] **V3.6** (Opsional) Tombol untuk batalkan rekaman - *belum diimplementasi*.
- [x] **V3.7** Redam warning `pycaw` saat boost volume.

### FASE V4 — Perbaikan Bug (BUGFIX) ✅ SELESAI
- [x] **V4.1** **Bug: program keluar sendiri saat startup.** Penyebab: tombol
      (termasuk Start & Kotak voice) ter-FALSE-TRIGGER di frame awal saat stik
      baru diinisialisasi. **Perbaikan:**
      - `JoystickReader.__init__` membuang event/state awal (5x pump).
      - **Grace period** `startup_grace_seconds` (default 2 detik): semua tombol
        diabaikan & di-sync tanpa memicu aksi.
      - `flush=True` pada banner agar output selalu tampil.
- [x] **V4.2** Verifikasi: 5x run berturut-turut tanpa false-trigger.
- [x] **V4.3** **Bug: tombol Enter (Segitiga) tidak merespons.** Penyebab: default
      `enter_hold_seconds = 0.6` (harus ditahan lama) + `press_enter` terikat
      state voice. **Perbaikan:**
      - Default `enter_hold_seconds` diubah **0.0** → Enter langsung saat diklik
        (edge-triggered).
      - `press_enter` dibuat **independen** dari state voice.
      - Opsi hold tetap tersedia (`enter_hold_seconds > 0`) bila diinginkan.
      - Log `[VOICE] Enter ditekan.` untuk memudahkan debug.

---

## 9. Detail Teknis Penting

### 9.1 Menangkap & Mengirim Audio
- `speech_recognition` bisa menangkap langsung dari mikrofon via
  `Recognizer.listen(mic)` lalu `.recognize_google(audio, language=...)`.
- **Masalah:** `listen()` bersifat blocking (menunggu sampai ada keheningan).
- **Solusi:** rekam ke file WAV saat RECORDING, stop saat tombol ditekan lagi,
  baru kirim file ke Google. Ini memberi kontrol penuh waktu (bukan auto-stop).

### 9.2 Freeze Mouse
- Saat RECORDING, `Controller` tidak memanggil `_update_mouse()`.
- Saat freeze, lepas semua tombol yang mungkin tertahan (`release_all()`).
- Setelah selesai, mouse kembali aktif normal.

### 9.3 Overlay Ikon Mic
- Pakai `tkinter`: `Toplevel` tanpa border (`overrideredirect(True)`),
  transparan (`-alpha`), selalu di atas (`-topmost`).
- Posisi mengikuti kursor (`mouse.position`), di-offset sedikit.
- Digambar manual pakai `Canvas` (lingkaran + ikon mic) → tanpa file gambar.
- Dijalankan di thread terpisah dengan komunikasi via queue/flag.

### 9.4 Ketik Teks via pynput
- `pynput.keyboard.Controller().type(text)` — mengetik string.
- Perlu hati-hati: keyboard layout berbeda bisa mengubah karakter.
- `typing_interval` kecil agar tidak "spam" aplikasi target.

### 9.5 Tombol Enter
- `keyboard.Controller().press(Key.enter)` + `release(Key.enter)`.

---

## 10. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Mikrofon tidak ada/bermasalah | Fitur tidak jalan | Verifikasi V0.1; notif jelas bila gagal |
| Internet mati saat STT | Gagal mengenali | Fallback ke Windows SAPI / notif |
| Google rate-limit | Gagal sementara | Pesan ramah, saran coba lagi |
| `listen()` blocking | Program "hang" | Rekam manual ke WAV, bukan auto-listen |
| Akurasi bahasa Indonesia sedang | Teks salah | Bisa ganti bahasa/engine di config |
| Overlay mengganggu fokus | Ganggu user | On-top tapi klik-lalu (click-through) |
| Tabrakan tombol dgn mode Gamepad | Aksi tak diinginkan | Abaikan voice di Gamepad mode |
| Teks terketik di aplikasi salah | Tidak nyaman | User tekan Enter manual (tidak auto) |

---

## 11. Definisi Selesai (Definition of Done)

Fitur dianggap selesai (v1.0) jika:
1. Tombol **Kotak** memulai & menghentikan rekaman (toggle).
2. Overlay ikon mic muncul saat merekam, hilang saat selesai.
3. Teks berbahasa Indonesia diketik otomatis dari hasil bicara.
4. Tombol **Segitiga** menekan Enter.
5. Mouse ter-freeze selama merekam.
6. Tidak crash saat mikrofon/internet bermasalah.
7. Tidak mengganggu fitur mouse yang sudah ada.

---

## 12. Pertanyaan Terbuka

1. **Ikon mic** — cukup gambar lingkaran+doodle, atau kamu punya file gambar ikon
   sendiri? (bisa disiapkan nanti)
2. **Durasi maksimal kata** — ada bayangan panjang kalimat yang ideal?
   (mempengaruhi tampilan overlay, bukan batas waktu)
3. **Fallback offline** — perlu disiapkan Windows SAPI sebagai cadangan, atau
   cukup Google saja untuk sekarang?
4. **Feedback suara** — perlu "bip" saat mulai/berhenti merekam? (butuh `winsound`)
5. **Tombol Segitiga = Enter** — apakah kamu khawatir Segitiga kebetulan ke-trigger
   (misal di game)? Perlu hold-to-enter?

---

## 13. Riwayat Perubahan

| Tanggal | Versi | Catatan |
|---|---|---|
| — | 0.1 | Draft awal: keputusan pengguna dicatat, arsitektur & task disusun. |
| — | 0.2 | FASE V0 selesai: verifikasi mic + Google Speech (Indonesia) berhasil. Temuan: volume mic harus di-boost. |
| — | 0.3 | FASE V1–V3 selesai: semua modul voice, integrasi tombol, freeze mouse, overlay, bip, robustness. Diverifikasi via mock test + end-to-end + smoke test. |
| — | 0.4 | FASE V4 (bugfix): perbaiki bug "program keluar sendiri saat startup" (false-trigger tombol) via grace period + flush event awal. |
| — | 0.5 | FASE V4.3: perbaiki tombol Enter (Segitiga) tidak merespons — default `enter_hold_seconds` jadi 0.0 (langsung), `press_enter` independen dari state voice. |

---

> **CATATAN:** Dokumen ini adalah rencana. **Belum ada kode yang ditulis.**
> Menunggu persetujuan pengguna & jawaban Bagian 12 sebelum eksekusi.
