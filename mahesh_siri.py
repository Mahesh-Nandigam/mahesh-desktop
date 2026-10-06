"""
⚡ MAHESH SIRI FOR WINDOWS (Unified Zero-Conflict Audio Engine)
- Single high-performance sounddevice stream (Zero device busy conflicts)
- Wakes up instantly on normal speaking voice or [Alt + M]
- Displays glowing Siri Dynamic Island on top of screen
- Speaks responses & auto-dismisses after 3 seconds
"""

import os
import sys
import time
import queue
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

SAMPLE_RATE = 16000
BLOCK_SIZE = 4000 # 0.25s chunks

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
        self.audio_queue = queue.Queue()

        # Start Unified Audio Engine & Hotkeys
        self.setup_hotkeys()
        threading.Thread(target=self.unified_audio_worker, daemon=True).start()

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

    def show_siri_ui(self, title="⚡ LISTENING...", text="Listening for command... (Speak now)", border="#00E5FF"):
        self.status_title.configure(text=title, text_color=border)
        self.transcript_label.configure(text=text, text_color="#F8FAFC")
        self.card.configure(border_color=border)

        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.is_active = True

    def process_and_respond(self, user_text: str):
        self.show_siri_ui(title="⚡ EXECUTING", text=f"\"{user_text}\"", border="#10B981")

        res = self.reasoning.process_command(user_text)
        reply = res.get("message", "Done!")

        self.status_title.configure(text="⚡ MAHESH", text_color="#10B981")
        self.transcript_label.configure(text=reply, text_color="#F8FAFC")

        # Speak verbally in thread
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

    def unified_audio_worker(self):
        """Unified audio capture that handles both wake-detection and transcription."""
        buffer_frames = []
        is_recording_command = False
        silence_chunks = 0

        def audio_callback(indata, frames, time_info, status):
            volume_norm = np.linalg.norm(indata) * 10
            self.audio_queue.put((indata.copy(), volume_norm))

        try:
            with sd.InputStream(callback=audio_callback, channels=1, samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE):
                while True:
                    try:
                        chunk, volume = self.audio_queue.get(timeout=0.5)

                        # Check if voice triggered
                        if not is_recording_command:
                            if volume > 0.85 and not self.is_active:
                                # Voice burst detected! Trigger wake chime and pop up UI
                                is_recording_command = True
                                silence_chunks = 0
                                buffer_frames = [chunk]
                                self.after(0, lambda: self.show_siri_ui(title="⚡ LISTENING...", text="Listening..."))
                                threading.Thread(target=self.play_siri_chime, daemon=True).start()
                        else:
                            buffer_frames.append(chunk)
                            if volume < 0.5:
                                silence_chunks += 1
                            else:
                                silence_chunks = 0

                            # End of speech detected (after ~1.0s of silence or 4s max)
                            if silence_chunks >= 4 or len(buffer_frames) >= 16:
                                is_recording_command = False
                                self.after(0, lambda: self.status_title.configure(text="🧠 THINKING...", text_color="#8B5CF6"))

                                # Convert audio buffer to speech_recognition AudioData
                                full_audio = np.concatenate(buffer_frames, axis=0)
                                audio_int16 = (full_audio * 32767).astype(np.int16)
                                audio_bytes = audio_int16.tobytes()

                                audio_data = sr.AudioData(audio_bytes, SAMPLE_RATE, 2)
                                threading.Thread(target=self._transcribe_audio, args=(audio_data,), daemon=True).start()
                                buffer_frames = []

                    except queue.Empty:
                        continue
        except Exception as e:
            print(f"[UnifiedAudio] Error: {e}")

    def _transcribe_audio(self, audio_data):
        try:
            transcript = self.recognizer.recognize_google(audio_data)
            print(f"[Transcribed]: {transcript}")
            self.after(0, lambda: self.process_and_respond(transcript))
        except sr.UnknownValueError:
            self.after(0, lambda: self.transcript_label.configure(text="I didn't catch that. Say 'Hey Mahesh' again."))
            self.after(0, lambda: self.schedule_auto_hide(2.0))
        except Exception as e:
            self.after(0, lambda: self.schedule_auto_hide(1.5))

    def setup_hotkeys(self):
        listener = keyboard.GlobalHotKeys({
            '<alt>+m': lambda: self.after(0, lambda: self.show_siri_ui(title="⚡ LISTENING...", text="Listening... (Speak now)")),
            '<alt>+s': lambda: self.after(0, lambda: self.process_and_respond("explain this slide"))
        })
        listener.daemon = True
        listener.start()

def create_tray_icon(app_instance):
    image = Image.new('RGB', (64, 64), color=(10, 11, 16))
    draw = ImageDraw.Draw(image)
    draw.ellipse([8, 8, 56, 56], fill=(0, 229, 255), outline=(139, 92, 246))

    menu = pystray.Menu(
        pystray.MenuItem("⚡ Wake Mahesh Siri (Alt+M)", lambda: app_instance.after(0, lambda: app_instance.show_siri_ui())),
        pystray.MenuItem("📸 Explain Screen (Alt+S)", lambda: app_instance.after(0, lambda: app_instance.process_and_respond("explain this slide"))),
        pystray.MenuItem("Exit", lambda icon: (icon.stop(), sys.exit(0)))
    )

    icon = pystray.Icon("MaheshSiri", image, "Mahesh Siri for Windows", menu)
    icon.run()

def main():
    print("[Mahesh Siri] Unified Zero-Conflict Audio Engine Running...")
    app = MaheshSiriWidget()
    threading.Thread(target=create_tray_icon, args=(app,), daemon=True).start()
    app.mainloop()

if __name__ == "__main__":
    main()
