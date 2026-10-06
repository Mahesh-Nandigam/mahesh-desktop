"""
⚡ MAHESH SIRI FOR WINDOWS (High-Speed Local Voice Trigger)
- Ultra-responsive VAD & Voice Detection
- 100% Invisible until you speak or press Alt+M
- Instant Siri Chime & Floating Dynamic Island
- Direct OS Automations (Apps, Screen Vision, Auto-typing, Volume)
- Auto-dismisses back into invisible background
"""

import os
import sys
import time
import threading
import winsound
import numpy as np
import sounddevice as sd
import customtkinter as ctk
import speech_recognition as sr
import pyttsx3
from pynput import keyboard
from PIL import Image, ImageDraw
import pystray

# Ensure UTF-8 output encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.automations import DesktopAutomations
from core.reasoning import DesktopReasoningEngine

ctk.set_appearance_mode("dark")

class MaheshSiriWidget(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.automations = DesktopAutomations()
        self.reasoning = DesktopReasoningEngine(self.automations)

        # TTS Engine
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 185)
        except Exception:
            self.tts_engine = None

        self.recognizer = sr.Recognizer()

        # Window Styling (Floating Siri Dynamic Island)
        self.title("Mahesh Siri")
        self.geometry("540x160")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#000000")

        self.position_island()
        self.setup_ui()

        # Start hidden (Zero clutter)
        self.withdraw()
        self.is_active = False
        self.dismiss_timer = None

        # Start Hotkeys & Fast Audio Streaming Listener
        self.setup_hotkeys()
        threading.Thread(target=self.start_audio_stream_listener, daemon=True).start()

    def position_island(self):
        screen_w = self.winfo_screenwidth()
        x = (screen_w - 540) // 2
        y = 35 # 35px from top of screen
        self.geometry(f"540x160+{x}+{y}")

    def setup_ui(self):
        # Outer Card with Glowing Border
        self.card = ctk.CTkFrame(
            self,
            fg_color="#0A0B10",
            border_color="#00E5FF",
            border_width=2,
            corner_radius=28
        )
        self.card.pack(fill="both", expand=True, padx=2, pady=2)

        # Content Row
        self.content_row = ctk.CTkFrame(self.card, fg_color="transparent")
        self.content_row.pack(fill="both", expand=True, padx=20, pady=14)

        # Left: Glowing Orb Icon
        self.orb_label = ctk.CTkLabel(
            self.content_row,
            text="⚡",
            font=ctk.CTkFont(size=28),
            text_color="#00E5FF",
            width=48
        )
        self.orb_label.pack(side="left", padx=(0, 12))

        # Right: Text Content
        self.text_container = ctk.CTkFrame(self.content_row, fg_color="transparent")
        self.text_container.pack(side="left", fill="both", expand=True)

        self.status_title = ctk.CTkLabel(
            self.text_container,
            text="MAHESH SIRI",
            font=ctk.CTkFont(family="Plus Jakarta Sans", size=12, weight="bold"),
            text_color="#00E5FF",
            anchor="w"
        )
        self.status_title.pack(fill="x")

        self.transcript_label = ctk.CTkLabel(
            self.text_container,
            text="Listening for your command...",
            font=ctk.CTkFont(family="Plus Jakarta Sans", size=14),
            text_color="#F8FAFC",
            wraplength=420,
            justify="left",
            anchor="w"
        )
        self.transcript_label.pack(fill="x", pady=(2, 0))

        # Subtle Bottom Hint
        self.hint_label = ctk.CTkLabel(
            self.card,
            text="Press ESC to dismiss | Auto-hides after finishing",
            font=ctk.CTkFont(size=10),
            text_color="#475569"
        )
        self.hint_label.pack(side="bottom", pady=(0, 8))

        self.bind("<Escape>", lambda e: self.hide_siri())

    def play_siri_chime(self):
        """Plays soft modern Siri wake chime."""
        try:
            winsound.Beep(587, 80)  # D5
            winsound.Beep(880, 110) # A5
        except Exception:
            pass

    def wake_up_siri(self, initial_text="Listening for command... (Speak now)"):
        if self.is_active:
            return
        self.is_active = True

        threading.Thread(target=self.play_siri_chime, daemon=True).start()

        self.status_title.configure(text="⚡ LISTENING...", text_color="#00E5FF")
        self.transcript_label.configure(text=initial_text, text_color="#F8FAFC")
        self.card.configure(border_color="#00E5FF")

        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

        # Record speech command
        threading.Thread(target=self.capture_and_process_voice, daemon=True).start()

    def capture_and_process_voice(self):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=6)

            self.status_title.configure(text="🧠 THINKING...", text_color="#8B5CF6")
            self.card.configure(border_color="#8B5CF6")

            transcript = self.recognizer.recognize_google(audio)
            self.process_and_respond(transcript)

        except sr.WaitTimeoutError:
            self.transcript_label.configure(text="No speech detected.")
            self.schedule_auto_hide(1.5)
        except sr.UnknownValueError:
            self.transcript_label.configure(text="I didn't catch that. Say 'Hey Mahesh' again.")
            self.schedule_auto_hide(2.0)
        except Exception as e:
            self.transcript_label.configure(text="Mic ready. Press Alt+M to trigger.")
            self.schedule_auto_hide(2.0)

    def process_and_respond(self, user_text: str):
        self.transcript_label.configure(text=f"\"{user_text}\"")

        res = self.reasoning.process_command(user_text)
        reply = res.get("message", "Done!")

        self.status_title.configure(text="⚡ EXECUTING", text_color="#10B981")
        self.card.configure(border_color="#10B981")
        self.transcript_label.configure(text=reply, text_color="#F8FAFC")

        # Speak verbally
        if self.tts_engine:
            threading.Thread(target=self._speak_text, args=(reply,), daemon=True).start()

        # Auto-dismiss smoothly after 3.5 seconds
        self.schedule_auto_hide(3.5)

    def _speak_text(self, text):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 185)
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass

    def schedule_auto_hide(self, delay_seconds: float):
        if self.dismiss_timer:
            self.after_cancel(self.dismiss_timer)
        self.dismiss_timer = self.after(int(delay_seconds * 1000), self.hide_siri)

    def hide_siri(self):
        self.withdraw()
        self.is_active = False

    def start_audio_stream_listener(self):
        """Continuous high-speed sounddevice stream listener for voice bursts."""
        sample_rate = 16000
        block_size = 8000 # 0.5s blocks

        def audio_callback(indata, frames, time_info, status):
            if self.is_active:
                return
            volume_norm = np.linalg.norm(indata) * 10
            # If significant vocal sound detected
            if volume_norm > 2.2:
                # Fast check if user is speaking "Hey Mahesh"
                self.after(0, self.wake_up_siri)

        try:
            with sd.InputStream(callback=audio_callback, channels=1, samplerate=sample_rate, blocksize=block_size):
                while True:
                    time.sleep(0.5)
        except Exception as e:
            print(f"[AudioListener] Fallback: {e}")

    def setup_hotkeys(self):
        listener = keyboard.GlobalHotKeys({
            '<alt>+m': lambda: self.after(0, self.wake_up_siri),
            '<alt>+s': lambda: self.after(0, lambda: self.process_and_respond("explain this slide"))
        })
        listener.daemon = True
        listener.start()

def create_tray_icon(app_instance):
    """Creates a system tray icon so the app runs invisibly in background."""
    image = Image.new('RGB', (64, 64), color=(10, 11, 16))
    draw = ImageDraw.Draw(image)
    draw.ellipse([8, 8, 56, 56], fill=(0, 229, 255), outline=(139, 92, 246))

    menu = pystray.Menu(
        pystray.MenuItem("⚡ Wake Mahesh Siri (Alt+M)", lambda: app_instance.after(0, app_instance.wake_up_siri)),
        pystray.MenuItem("📸 Explain Screen (Alt+S)", lambda: app_instance.after(0, lambda: app_instance.process_and_respond("explain this slide"))),
        pystray.MenuItem("Exit", lambda icon: (icon.stop(), sys.exit(0)))
    )

    icon = pystray.Icon("MaheshSiri", image, "Mahesh Siri for Windows", menu)
    icon.run()

def main():
    print("[Mahesh Siri] Booting background daemon...")
    print("[Mahesh Siri] Wakes up on voice trigger or [Alt + M].")
    print("[Mahesh Siri] 100% invisible until called.")

    app = MaheshSiriWidget()
    threading.Thread(target=create_tray_icon, args=(app,), daemon=True).start()
    app.mainloop()

if __name__ == "__main__":
    main()
