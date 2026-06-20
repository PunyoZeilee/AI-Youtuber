#  Hana VTuber Bot

AI YouTube Live Bot bernama **Hana** — seorang mahasiswi tingkat akhir Informatika yang "terpaksa" jadi VTuber. Bot ini membaca komentar dari YouTube Live Chat, menjawabnya dengan AI dalam Bahasa Indonesia, mengubah jawaban jadi suara (TTS), dan menampilkan subtitle di overlay window.

##  Fitur

- 💬 Membaca YouTube Live Chat secara real-time (`pytchat`)
- 🧠 AI jawab otomatis pakai **Groq API** (gratis & cepat, tanpa VPN)
- 🗣️ Text-to-Speech Bahasa Indonesia pakai **gTTS**
- 🔊 Audio playback otomatis pakai **pygame**
- 📝 Subtitle overlay window (Tkinter) untuk ditampilkan di OBS/streaming software
- 🎭 Karakter custom: mahasiswi semester akhir yang santai, ramah, dan sering curhat soal skripsi

##  Arsitektur Singkat

```
YouTube Live Chat ──▶ pytchat ──▶ Queue ──▶ Groq AI ──▶ gTTS ──▶ pygame (audio)
                                                            │
                                                            ▼
                                                  Tkinter Subtitle Window
```

- **Main thread**: membaca chat YouTube (pytchat wajib jalan di main thread)
- **Thread asyncio**: memproses pesan → tanya AI → text-to-speech
- **Thread Tkinter**: menampilkan subtitle overlay

##  Requirements

- Python 3.9+
- Koneksi internet
- Akun [Groq Console](https://console.groq.com/) (gratis) untuk API key

##  Instalasi

1. Clone/download project ini, lalu install dependency:

   ```bash
   pip install pytchat groq gTTS pygame requests
   ```

   > `tkinter` biasanya sudah bawaan Python. Kalau belum ada (umumnya di Linux), install lewat package manager OS, misalnya:
   > ```bash
   > sudo apt install python3-tk
   > ```

2. **Dapatkan Groq API Key (gratis, tanpa VPN):**
   1. Buka [https://console.groq.com/](https://console.groq.com/)
   2. Daftar / login pakai akun Google
   3. Klik **API Keys** → **Create API Key**
   4. Copy key yang muncul

3. **Set API key sebagai environment variable** — jangan hardcode langsung di kode, supaya key tidak bocor kalau project ini di-share atau di-push ke Git:

   **Linux/macOS:**
   ```bash
   export GROQ_API_KEY="masukkan-key-kamu-disini"
   ```

   **Windows (PowerShell):**
   ```powershell
   $env:GROQ_API_KEY="masukkan-key-kamu-disini"
   ```

   Lalu di `hana_bot.py`, ambil key dari environment:
   ```python
   import os
   GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
   ```

   > ⚠️ **Penting:** Jangan pernah commit API key ke repository publik (GitHub, dsb). Kalau key kamu pernah tertulis langsung di kode dan sudah di-share/upload ke mana pun, segera **revoke** key tersebut di console.groq.com dan buat key baru.

4. **Isi YouTube Video ID** di bagian konfigurasi script:

   ```python
   YOUTUBE_VIDEO_ID = "ID_VIDEO_LIVE_YOUTUBE_KAMU"
   ```

   ID video ini adalah bagian setelah `v=` di URL YouTube Live kamu, contoh:
   `https://www.youtube.com/watch?v=ABCDEFG1234` → ID-nya `ABCDEFG1234`

##  Cara Menjalankan

```bash
python hana_bot.py
```

Setelah berjalan:
- Bot otomatis konek ke live chat YouTube (akan retry tiap 10 detik kalau live belum mulai)
- Subtitle window kecil akan muncul di pojok kiri atas layar — bisa kamu capture lewat OBS sebagai overlay
- Setiap komentar yang masuk akan dijawab Hana lewat suara + subtitle

Tekan `Ctrl + C` di terminal untuk menghentikan bot.

##  Mengubah Karakter / Persona

Persona Hana diatur lewat variabel `SYSTEM_PROMPT` di dalam script. Kamu bisa edit bagian ini untuk:
- Mengubah nama dan latar belakang karakter
- Mengubah gaya bahasa (formal/santai)
- Mengubah aturan panjang jawaban
- Menambah topik yang sering dia bahas

##  Konfigurasi Tambahan

| Variabel | Fungsi | Lokasi |
|---|---|---|
| `GROQ_MODEL` | Model AI yang dipakai (`llama-3.1-8b-instant` lebih cepat, `llama-3.3-70b-versatile` lebih pintar) | bagian konfigurasi |
| `_api_min_interval` | Jeda minimal antar request ke Groq, untuk menghindari rate limit | dekat fungsi `tanya_groq` |
| `SUBTITLE_DELAY_MS` | Delay sinkronisasi antara audio mulai dan subtitle muncul | dekat fungsi `hana_bicara` |

##  Troubleshooting

- **`❌ Groq tidak tersedia`** → pastikan `pip install groq` sudah jalan dan API key valid.
- **`⚠️ pytchat tidak tersedia`** → jalankan `pip install pytchat`.
- **Subtitle window tidak muncul** → pastikan `tkinter` terinstall di sistem (lihat langkah instalasi di atas).
- **Tidak ada suara** → pastikan `pygame` dan `gTTS` terinstall, serta koneksi internet aktif (gTTS butuh internet untuk generate audio).
- **`[Groq] ⚠️ Rate limit!`** → bot akan otomatis menunggu sebelum mencoba lagi; ini normal di free tier kalau trafik chat tinggi.
- **Live tidak terdeteksi** → pastikan `YOUTUBE_VIDEO_ID` benar dan stream sudah live (bukan masih scheduled).

##  Struktur File

```
.
├── hana_bot.py     # Script utama
└── README.md       # Dokumentasi ini
```

##  Catatan Keamanan

- **Jangan hardcode API key langsung di source code**, terutama jika file ini akan di-share, di-upload, atau di-push ke repository publik.
- Gunakan environment variable atau file `.env` (dengan library seperti `python-dotenv`) untuk menyimpan key secara aman.
- Jika API key pernah ter-expose secara tidak sengaja, segera revoke dan generate key baru di [console.groq.com](https://console.groq.com/).

##  Lisensi

Bebas digunakan dan dimodifikasi untuk keperluan pribadi/streaming.
