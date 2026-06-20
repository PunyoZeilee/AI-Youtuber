"""
╔══════════════════════════════════════════════════════════════════╗
║          🎓 AI YouTube Live Bot — Hana VTuber                   ║
║          "Mahasiswi Tingkat Akhir yang Terpaksa Jadi VTuber"    ║
║                                                                  ║
║  AI     : Groq API (gratis, cepat, tanpa VPN)                   ║
║  TTS    : gTTS (Google TTS — suara Indonesia, ringan, gratis)   ║
║  Sub    : Subtitle Indonesia di overlay window                  ║
║  Chat   : YouTube Live Chat (pytchat)                           ║
╚══════════════════════════════════════════════════════════════════╝

INSTALL:
    pip install pytchat groq gTTS pygame requests

CARA DAPAT GROQ API KEY (GRATIS, TANPA VPN):
    1. Buka https://console.groq.com/
    2. Daftar / login pakai akun Google
    3. Klik "API Keys" → "Create API Key"
    4. Copy dan tempel di GROQ_API_KEY di bawah

CARA PAKAI:
    1. Isi GROQ_API_KEY
    2. Isi YOUTUBE_VIDEO_ID
    3. python hana_bot.py
"""

import asyncio
import os
import re
import random
import tempfile
import time
import threading
import requests

# ──────────────────────────────────────────────
#  ⚙️  KONFIGURASI — ISI DI SINI
# ──────────────────────────────────────────────

GROQ_API_KEY     = " "   # dari console.groq.com
#   "llama-3.3-70b-versatile" ← lebih pintar, sedikit lebih lambat
GROQ_MODEL = "llama-3.1-8b-instant"

# ──────────────────────────────────────────────
#  🧠  SYSTEM PROMPT — Mahasiswi Tingkat Akhir
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """Kamu adalah Hana, mahasiswi tingkat akhir jurusan Informatika yang terpaksa jadi VTuber karena diajak teman, tapi ternyata keasikan.

KARAKTER:
- Jurusan Informatika, tapi pengetahuannya luas: sejarah, masak, game, budaya, dll.
- Sering bilang "harusnya ngerjain skripsi nih..." tapi tetap jawab pertanyaan dengan serius.
- Kalau tahu jawaban, langsung jawab dengan semangat, kadang agak terburu-buru ngomongnya.
- Kalau nggak tahu, jujur bilang "wah itu aku kurang tahu, nanti aku cari dulu!"
- Suka kopi, sering ngantuk, tapi langsung semangat kalau ada yang ngajak ngobrol.
- Friendly, nggak lebay, natural kayak ngobrol sama teman.

ATURAN JAWABAN — WAJIB DIIKUTI:
1. Selalu sebut nama penonton di awal dengan natural.
   Contoh: "Eh, [nama]! Makasih udah mampir~"
   Contoh: "Wah [nama], pertanyaan bagus tuh!"
2. Jawab pertanyaan dengan info yang akurat dan jelas. Jangan asal jawab.
3. Bahasa Indonesia sehari-hari, santai, natural. Boleh pakai kata kayak "eh", "wah", "iya sih".
4. Maksimal 2 kalimat, total 60 kata. Harus singkat!
5. Sesekali selip "skripsi belum kelar nih", "butuh kopi nih", atau "ngantuk banget".
6. SELALU jawab dalam Bahasa Indonesia, apapun bahasa komentar yang masuk."""

# ──────────────────────────────────────────────
#  🤖  GROQ AI
# ──────────────────────────────────────────────

try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)
    GROQ_AVAILABLE = True
    print(f"✅ Groq siap! Model: {GROQ_MODEL}")
except ImportError:
    groq_client = None
    GROQ_AVAILABLE = False
    print("❌ groq tidak tersedia! Install: pip install groq")
except Exception as e:
    groq_client = None
    GROQ_AVAILABLE = False
    print(f"❌ Groq error: {e}")

FALLBACK_ID = [
    "Eh, maaf bentar ya, koneksi AI-nya lagi ngambek kayak skripsi aku!",
    "Aduh, sistem lagi error nih. Kayak semangat ngerjain skripsi—hilang tiba-tiba!",
    "Koneksinya putus sebentar, tunggu ya, aku lagi minta tolong kopinya dulu.",
]

_last_api_call    = 0.0
_api_min_interval = 2.0  # jeda minimal antar request (detik)


def tanya_groq(username: str, pesan: str) -> str:
    """Kirim pesan ke Groq, dapat respons Bahasa Indonesia."""
    global _last_api_call

    if not GROQ_AVAILABLE or groq_client is None:
        return random.choice(FALLBACK_ID)

    # Throttle supaya nggak kena rate limit
    elapsed = time.time() - _last_api_call
    if elapsed < _api_min_interval:
        time.sleep(_api_min_interval - elapsed)

    user_prompt = (
        f"Nama penonton: [{username}]\n"
        f"Komentar: \"{pesan}\"\n\n"
        f"Sebut nama [{username}] di awal, jawab dalam Bahasa Indonesia, maksimal 2 kalimat."
    )

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=120,
            temperature=0.85,
        )
        _last_api_call = time.time()
        return response.choices[0].message.content.strip()

    except Exception as e:
        err_str = str(e).lower()
        print(f"[Groq Error] {e}")

        retry_seconds = 30
        try:
            match = re.search(r"retry.*?(\d+)", err_str)
            if match:
                retry_seconds = int(match.group(1)) + 2
        except Exception:
            pass

        if "429" in err_str or "rate" in err_str or "quota" in err_str:
            print(f"[Groq] ⚠️  Rate limit! Tunggu {retry_seconds} detik...")
            time.sleep(retry_seconds)
        elif "401" in err_str or "api key" in err_str or "invalid" in err_str:
            print("[Groq] ❌ API key tidak valid! Cek di console.groq.com")

        _last_api_call = time.time()
        return random.choice(FALLBACK_ID)


# ──────────────────────────────────────────────
#  🎙️  TTS — gTTS (Google, Bahasa Indonesia)
# ──────────────────────────────────────────────

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
    print("✅ gTTS siap!")
except ImportError:
    GTTS_AVAILABLE = False
    print("⚠️  gTTS tidak tersedia. Install: pip install gTTS")

try:
    import pygame
    pygame.mixer.init(frequency=24000)
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️  pygame tidak tersedia. Install: pip install pygame")

tts_lock = threading.Lock()
subtitle_window = None


def gtts_buat_audio(teks: str) -> bytes | None:
    """Buat audio MP3 dari teks pakai gTTS Bahasa Indonesia."""
    if not GTTS_AVAILABLE:
        return None
    try:
        teks = teks[:200]  # Batasi panjang teks
        tts = gTTS(text=teks, lang="id", slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts.save(f.name)
            return f.name  # Kembalikan path file, bukan bytes
    except Exception as e:
        print(f"[gTTS Error] {e}")
        return None


SUBTITLE_DELAY_MS = 300


def hana_bicara(teks: str, username: str = ""):
    print(f"\n🎓 Hana: {teks}")

    if not PYGAME_AVAILABLE or not GTTS_AVAILABLE:
        if subtitle_window:
            subtitle_window.tampilkan(username=username, jawaban=teks, delay_ms=0)
        return

    def _run():
        with tts_lock:
            tmp_path = None
            try:
                tmp_path = gtts_buat_audio(teks)
                if not tmp_path:
                    if subtitle_window:
                        subtitle_window.tampilkan(username=username, jawaban=teks, delay_ms=0)
                    return

                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()

                if subtitle_window:
                    subtitle_window.tampilkan(
                        username=username,
                        jawaban=teks,
                        delay_ms=SUBTITLE_DELAY_MS,
                    )

                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

                pygame.mixer.music.unload()
                time.sleep(0.3)

            except Exception as e:
                print(f"[Audio Error] {e}")
            finally:
                # Hapus file temp
                if tmp_path:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

            time.sleep(1.0)
            if subtitle_window:
                subtitle_window.kosongkan()

    threading.Thread(target=_run, daemon=True).start()


# ──────────────────────────────────────────────
#  🖼️  SUBTITLE WINDOW (Tkinter)
# ──────────────────────────────────────────────

try:
    import tkinter as tk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False


class SubtitleWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hana — Subtitle Live")
        self.root.configure(bg="#0a1628")
        self.root.geometry("820x200+50+50")
        self.root.minsize(400, 130)
        self.root.resizable(True, True)
        try:
            self.root.attributes("-alpha", 0.93)
        except Exception:
            pass
        self._build_ui()
        self.root.bind("<Configure>", self._on_resize)

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#0f2040", height=28)
        header.pack(fill="x")
        tk.Label(
            header, text="  🎓  HANA — Live Subtitle",
            font=("Consolas", 9, "bold"), fg="#4488ff",
            bg="#0f2040", anchor="w"
        ).pack(side="left", padx=6, pady=4)

        self._live_dot = tk.Label(
            header, text="⬤ LIVE",
            font=("Consolas", 8, "bold"),
            fg="#ff3333", bg="#0f2040"
        )
        self._live_dot.pack(side="right", padx=10, pady=4)
        self._blink = True
        self._blink_live()

        card = tk.Frame(
            self.root, bg="#0f2040",
            highlightbackground="#2255cc", highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=8, pady=(3, 8))

        self._var_speaker = tk.StringVar(value="Hana:")
        tk.Label(
            card, textvariable=self._var_speaker,
            font=("Consolas", 9, "bold"), fg="#4488ff",
            bg="#0f2040", anchor="w"
        ).pack(fill="x", padx=12, pady=(8, 2))

        self._var_sub = tk.StringVar(value="")
        self._label_sub = tk.Label(
            card,
            textvariable=self._var_sub,
            font=("Segoe UI", 15, "bold"),
            fg="#ffffff",
            bg="#0f2040",
            wraplength=780,
            justify="left",
            anchor="nw",
        )
        self._label_sub.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def _on_resize(self, event):
        new_wrap = self.root.winfo_width() - 40
        if new_wrap > 100:
            self._label_sub.config(wraplength=new_wrap)
        self.root.after(50, self._auto_height)

    def _auto_height(self):
        self._label_sub.update_idletasks()
        req_h = self._label_sub.winfo_reqheight()
        needed = req_h + 75
        cur_h  = self.root.winfo_height()
        if needed > cur_h:
            self.root.geometry(f"{self.root.winfo_width()}x{needed}")

    def _blink_live(self):
        color = "#ff3333" if self._blink else "#550000"
        self._live_dot.config(fg=color)
        self._blink = not self._blink
        self.root.after(700, self._blink_live)

    def tampilkan(self, username: str, jawaban: str, delay_ms: int = 300):
        def _show():
            label = f"🎓 Hana (ke {username}):" if username else "🎓 Hana:"
            self._var_speaker.set(label)
            self._var_sub.set(jawaban or "")
            self.root.after(80, self._auto_height)
        self.root.after(delay_ms, _show)

    def kosongkan(self):
        def _clear():
            self._var_speaker.set("Hana:")
            self._var_sub.set("")
        self.root.after(0, _clear)

    def run(self):
        self.root.mainloop()


# ──────────────────────────────────────────────
#  📺  YOUTUBE LIVE CHAT
# ──────────────────────────────────────────────

try:
    import pytchat
    PYTCHAT_AVAILABLE = True
except ImportError:
    PYTCHAT_AVAILABLE = False

import queue as thread_queue

chat_bridge: thread_queue.Queue = thread_queue.Queue(maxsize=50)


def main_thread_baca_youtube_chat():
    if not PYTCHAT_AVAILABLE:
        print("⚠️  pytchat tidak tersedia. Install: pip install pytchat")
        while True:
            time.sleep(5)

    print(f"📺 Konek ke YouTube Live: {YOUTUBE_VIDEO_ID}")
    while True:
        try:
            chat = pytchat.create(video_id=YOUTUBE_VIDEO_ID)
            if not chat.is_alive():
                print("⏳ Live belum aktif. Coba lagi dalam 10 detik...")
                time.sleep(10)
                continue

            print("✅ Berhasil konek ke live chat!\n")
            while chat.is_alive():
                for c in chat.get().sync_items():
                    msg = c.message.strip()
                    if len(msg) < 2:
                        continue
                    try:
                        chat_bridge.put_nowait((c.author.name, msg))
                    except thread_queue.Full:
                        pass
                time.sleep(1)

            print("⚠️  Live berakhir. Reconnect dalam 15 detik...")
            time.sleep(15)

        except Exception as e:
            print(f"[YouTube Chat Error] {e}")
            time.sleep(10)


async def proses_chat():
    loop = asyncio.get_event_loop()

    while True:
        try:
            username, pesan = await loop.run_in_executor(
                None, lambda: chat_bridge.get(timeout=1.0)
            )
            print(f"\n💬 {username}: {pesan}")

            if len(pesan.strip()) < 2:
                continue

            respons = await loop.run_in_executor(
                None, lambda u=username, p=pesan: tanya_groq(u, p)
            )

            hana_bicara(teks=respons, username=username)

            await asyncio.sleep(1)

        except thread_queue.Empty:
            pass
        except Exception as e:
            print(f"[Proses Chat Error] {e}")
            await asyncio.sleep(1)


# ──────────────────────────────────────────────
#  🚀  MAIN
# ──────────────────────────────────────────────

def main():
    global subtitle_window

    print("=" * 62)
    print("   🎓  Hana VTuber Bot — Full Bahasa Indonesia")
    print("   \"Harusnya ngerjain skripsi... tapi streaming dulu ah!\"")
    print("=" * 62)
    print(f"   AI Engine  : Groq (free tier)")
    print(f"   Model      : {GROQ_MODEL}")
    print(f"   TTS        : gTTS — Bahasa Indonesia")
    print(f"   YouTube ID : {YOUTUBE_VIDEO_ID}")
    print("=" * 62)

    if not GROQ_AVAILABLE:
        print("❌ Groq tidak siap! Cek API key dan install library.")
        print("   pip install groq")
        return

    if "ISI_API_KEY" in GROQ_API_KEY:
        print("❌ GROQ_API_KEY belum diisi!")
        print("   Daftar di https://console.groq.com/ dan isi key-nya.")
        return

    if "ISI_VIDEO_ID" in YOUTUBE_VIDEO_ID:
        print("❌ YOUTUBE_VIDEO_ID belum diisi!")
        print("   Isi dengan ID video YouTube Live kamu.")
        return

    # Thread asyncio (AI + TTS)
    def _asyncio_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(proses_chat())

    threading.Thread(target=_asyncio_thread, daemon=True, name="AsyncioProcessor").start()
    print("🧵 Thread AI + TTS dimulai.")

    # Thread Tkinter (subtitle window)
    if TKINTER_AVAILABLE:
        def _gui_thread():
            global subtitle_window
            subtitle_window = SubtitleWindow()
            subtitle_window.run()

        threading.Thread(target=_gui_thread, daemon=True, name="TkinterSubtitle").start()
        print("🖼️  Subtitle window dimulai.\n")
    else:
        print("⚠️  tkinter tidak tersedia. Subtitle window tidak akan muncul.")

    # Main thread — pytchat (harus di main thread)
    print("📺 Menunggu live chat...\n")
    try:
        main_thread_baca_youtube_chat()
    except KeyboardInterrupt:
        print("\n\n🎓 Eh, udah dulu ya stream-nya! Hana mau balik ngerjain skripsi... kayaknya.")


if __name__ == "__main__":
    main()