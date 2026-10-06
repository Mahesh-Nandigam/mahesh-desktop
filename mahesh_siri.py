"""
⚡ MAHESH SIRI FOR WINDOWS (Single-Message-Pump Deadlock-Free)
- Sleek Floating Siri Island anchored to top of screen
- Real-time Audio Level Visualizer
- Instant Voice Trigger & Global Shortcut (Alt + M / Alt + S)
- Zero Window-Station / Thread-Lock Bugs
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
        self.recognizer = sr.Recognizer()

        # Window Styling (Floating Siri Dynamic Island)
        self.title("Mahesh Siri")
        self.geometry("540x95")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#000000")

        self.position_island()
        self.setup_ui()

        self.is_active = False
        self.dismiss_timer = None
        self.audio_queue = queue.Queue()

        # Start Unified Audio Engine & Global Hotkeys
        self.setup_hotkeys()
        threading.Thread(target=self.unified_audio_worker, daemon=True).start()

    def position_island(self):
        screen_w = self.winfo_screenwidth()
        x = (screen_w - 540) // 2
        y = 30 # 30px from top of screen
        self.geometry(f"540x95+{x}+{y}")

    def setup_ui(self):
        # Outer Card with Glowing Border
        self.card = ctk.CTkFrame(
            self,
            fg_color="#0A0B10",
            border_color="#00E5FF",
            border_width=2,
            corner_radius=24
        )
        self.card.pack(fill="both", expand=True, padx=2, pady=2)

        # Content Row
        self.content_row = ctk.CTkFrame(self.card, fg_color="transparent")
        self.content_row.pack(fill="both", expand=True, padx=16, pady=10)

        # Left: Glowing Orb Icon
        self.orb_btn = ctk.CTkButton(
            self.content_row,
            text="⚡",
            font=ctk.CTkFont(size=22),
            fg_color="#121520",
            hover_color="#00E5FF",
            text_color="#00E5FF",
            width=42,
            height=42,
            corner_radius=21,
            command=self.manual_trigger
        )
        self.orb_btn.pack(side="left", padx=(0, 10))

        # Right: Text Content
        self.text_container = ctk.CTkFrame(self.content_row, fg_color="transparent")
        self.text_container.pack(side="left", fill="both", expand=True)

        self.status_title = ctk.CTkLabel(
            self.text_container,
            text="MAHESH SIRI (STANDBY)",
            font=ctk.CTkFont(family="Plus Jakarta Sans", size=11, weight="bold"),
            text_color="#00E5FF",
            anchor="w"
        )
        self.status_title.pack(fill="x")

        self.transcript_label = ctk.CTkLabel(
            self.text_container,
            text="Say 'Hey Mahesh' or click the orb to speak...",
            font=ctk.CTkFont(family="Plus Jakarta Sans", size=13),
            text_color="#CBD5E1",
            wraplength=410,
            justify="left",
            anchor="w"
        )
        self.transcript_label.pack(fill="x", pady=(2, 0))

        # Close / Minimize button
        self.close_btn = ctk.CTkButton(
            self.content_row,
            text="✕",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#EF4444",
            text_color="#64748B",
            width=24,
            height=24,
            command=lambda: self.geometry("120x45") # Minimize to pill
        )
        self.close_btn.pack(side="right", padx=(4, 0))

    def play_siri_chime(self):
        try:
            winsound.Beep(587, 80)
            winsound.Beep(880, 110)
        except Exception:
            pass

    def manual_trigger(self):
        self.show_siri_ui(title="⚡ LISTENING...", text="Listening for command... (Speak now)", border="#00E5FF")

    def show_siri_ui(self, title="⚡ LISTENING...", text="Listening...", border="#00E5FF"):
        self.geometry("540x95")
        self.status_title.configure(text=title, text_color=border)
        self.transcript_label.configure(text=text, text_color="#F8FAFC")
        self.card.configure(border_color=border)
        self.is_active = True

    def process_and_respond(self, user_text: str):
        self.show_siri_ui(title="⚡ EXECUTING", text=f"\"{user_text}\"", border="#10B981")

        res = self.reasoning.process_command(user_text)
        reply = res.get("message", "Done!")

        self.status_title.configure(text="⚡ MAHESH", text_color="#10B981")
        self.transcript_label.configure(text=reply, text_color="#F8FAFC")

        threading.Thread(target=self._speak_text, args=(reply,), daemon=True).start()
        self.schedule_auto_reset(4.0)

    def _speak_text(self, text):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 185)
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass

    def schedule_auto_reset(self, delay_seconds: float):
        if self.dismiss_timer:
            self.after_cancel(self.dismiss_timer)
        self.dismiss_timer = self.after(int(delay_seconds * 1000), self.reset_to_standby)

    def reset_to_standby(self):
        self.status_title.configure(text="MAHESH SIRI (STANDBY)", text_color="#00E5FF")
        self.transcript_label.configure(text="Say 'Hey Mahesh' or click the orb to speak...", text_color="#CBD5E1")
        self.card.configure(border_color="#00E5FF")
        self.is_active = False

    def unified_audio_worker(self):
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

                        if not is_recording_command:
                            # Voice threshold tuned to laptop mic
                            if volume > 0.75 and not self.is_active:
                                is_recording_command = True
                                silence_chunks = 0
                                buffer_frames = [chunk]
                                self.after(0, lambda: self.show_siri_ui(title="⚡ LISTENING...", text="Listening..."))
                                threading.Thread(target=self.play_siri_chime, daemon=True).start()
                        else:
                            buffer_frames.append(chunk)
                            if volume < 0.45:
                                silence_chunks += 1
                            else:
                                silence_chunks = 0

                            if silence_chunks >= 4 or len(buffer_frames) >= 16:
                                is_recording_command = False
                                self.after(0, lambda: self.status_title.configure(text="🧠 THINKING...", text_color="#8B5CF6"))

                                full_audio = np.concatenate(buffer_frames, axis=0)
                                audio_int16 = (full_audio * 32767).astype(np.int16)
                                audio_bytes = audio_int16.tobytes()

                                audio_data = sr.AudioData(audio_bytes, SAMPLE_RATE, 2)
                                threading.Thread(target=self._transcribe_audio, args=(audio_data,), daemon=True).start()
                                buffer_frames = []

                    except queue.Empty:
                        continue
        except Exception as e:
            print(f"[AudioEngine] Stream Error: {e}")

    def _transcribe_audio(self, audio_data):
        try:
            transcript = self.recognizer.recognize_google(audio_data)
            print(f"[Transcribed]: {transcript}")
            self.after(0, lambda: self.process_and_respond(transcript))
        except sr.UnknownValueError:
            self.after(0, lambda: self.transcript_label.configure(text="I didn't catch that. Say 'Hey Mahesh' again."))
            self.after(0, lambda: self.schedule_auto_reset(2.5))
        except Exception as e:
            self.after(0, lambda: self.schedule_auto_reset(2.0))

    def setup_hotkeys(self):
        listener = keyboard.GlobalHotKeys({
            '<alt>+m': lambda: self.after(0, self.manual_trigger),
            '<alt>+s': lambda: self.after(0, lambda: self.process_and_respond("explain this slide"))
        })
        listener.daemon = True
        listener.start()

def main():
    print("[Mahesh Siri] Starting Deadlock-Free Siri Island...")
    app = MaheshSiriWidget()
    app.mainloop()

if __name__ == "__main__":
    main()
