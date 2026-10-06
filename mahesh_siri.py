"""
⚡ MAHESH SIRI FOR WINDOWS (Hybrid Voice + Stealth Typing Engine)
- Visible Real-Time Audio Level Meter (Visual confirmation of mic input)
- Instant Voice Transcription + Keyboard Typing in same bar
- High-Speed OS Actions (Apps, Screen Vision, Auto-typing, Volume)
- Global Hotkeys [Alt + M] & [Alt + S]
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
BLOCK_SIZE = 2000 # 0.125s chunks for ultra-fast visualizer updates

class MaheshSiriWidget(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.automations = DesktopAutomations()
        self.reasoning = DesktopReasoningEngine(self.automations)
        self.recognizer = sr.Recognizer()

        # Window Styling (Floating Siri Dynamic Island)
        self.title("Mahesh Siri")
        self.geometry("620x110")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#000000")

        self.position_island()
        self.setup_ui()

        self.is_recording = False
        self.audio_frames = []
        self.audio_queue = queue.Queue()

        # Start Unified Audio Engine & Global Hotkeys
        self.setup_hotkeys()
        threading.Thread(target=self.audio_stream_worker, daemon=True).start()

    def position_island(self):
        screen_w = self.winfo_screenwidth()
        x = (screen_w - 620) // 2
        y = 30 # 30px from top of screen
        self.geometry(f"620x110+{x}+{y}")

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

        # Top Header Bar inside card
        self.header_row = ctk.CTkFrame(self.card, fg_color="transparent")
        self.header_row.pack(fill="x", padx=16, pady=(10, 2))

        self.logo_label = ctk.CTkLabel(
            self.header_row,
            text="⚡ MAHESH SIRI",
            font=ctk.CTkFont(family="Plus Jakarta Sans", size=12, weight="bold"),
            text_color="#00E5FF"
        )
        self.logo_label.pack(side="left")

        # Audio Level Bar (Visual indicator of mic hearing sound)
        self.level_bar = ctk.CTkProgressBar(
            self.header_row,
            width=120,
            height=8,
            progress_color="#00E5FF",
            fg_color="#1E2230"
        )
        self.level_bar.set(0.0)
        self.level_bar.pack(side="left", padx=14)

        self.status_label = ctk.CTkLabel(
            self.header_row,
            text="● Listening...",
            font=ctk.CTkFont(size=11),
            text_color="#10B981"
        )
        self.status_label.pack(side="left")

        self.shortcut_hint = ctk.CTkLabel(
            self.header_row,
            text="Alt+M: Focus | Alt+S: Screen Eye",
            font=ctk.CTkFont(size=10),
            text_color="#64748B"
        )
        self.shortcut_hint.pack(side="right")

        # Input & Action Row
        self.action_row = ctk.CTkFrame(self.card, fg_color="transparent")
        self.action_row.pack(fill="x", padx=16, pady=(4, 10))

        # Glowing Mic Button (Click to toggle voice recording)
        self.mic_btn = ctk.CTkButton(
            self.action_row,
            text="🎙️",
            font=ctk.CTkFont(size=18),
            fg_color="#1E2230",
            hover_color="#00E5FF",
            text_color="#00E5FF",
            width=40,
            height=40,
            corner_radius=20,
            command=self.toggle_mic_recording
        )
        self.mic_btn.pack(side="left", padx=(0, 10))

        # Command Input Field (For hybrid silent typing or voice display)
        self.input_field = ctk.CTkEntry(
            self.action_row,
            placeholder_text="Speak or type command (e.g. 'battery status', 'open vs code', 'explain slide')...",
            font=ctk.CTkFont(family="Plus Jakarta Sans", size=13),
            fg_color="#141722",
            border_color="#2D3748",
            border_width=1,
            text_color="#F8FAFC",
            height=40,
            corner_radius=12
        )
        self.input_field.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input_field.bind("<Return>", lambda e: self.on_text_submit())

        # Run Button
        self.run_btn = ctk.CTkButton(
            self.action_row,
            text="Run",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#00E5FF",
            hover_color="#7C3AED",
            text_color="#000",
            width=55,
            height=40,
            corner_radius=12,
            command=self.on_text_submit
        )
        self.run_btn.pack(side="right")

    def play_siri_chime(self):
        try:
            winsound.Beep(587, 80)
            winsound.Beep(880, 110)
        except Exception:
            pass

    def on_text_submit(self):
        query = self.input_field.get().strip()
        if not query:
            return
        self.input_field.delete(0, "end")
        self.execute_command(query)

    def toggle_mic_recording(self):
        if not self.is_recording:
            self.start_manual_recording()
        else:
            self.stop_and_process_recording()

    def start_manual_recording(self):
        self.is_recording = True
        self.audio_frames = []
        self.mic_btn.configure(fg_color="#EF4444", text_color="#FFF")
        self.status_label.configure(text="● Recording voice...", text_color="#EF4444")
        self.card.configure(border_color="#EF4444")
        self.play_siri_chime()

    def stop_and_process_recording(self):
        self.is_recording = False
        self.mic_btn.configure(fg_color="#1E2230", text_color="#00E5FF")
        self.status_label.configure(text="🧠 Transcribing...", text_color="#8B5CF6")
        self.card.configure(border_color="#8B5CF6")

        if self.audio_frames:
            full_audio = np.concatenate(self.audio_frames, axis=0)
            audio_int16 = (full_audio * 32767).astype(np.int16)
            audio_data = sr.AudioData(audio_int16.tobytes(), SAMPLE_RATE, 2)
            threading.Thread(target=self._transcribe_audio, args=(audio_data,), daemon=True).start()
        self.audio_frames = []

    def execute_command(self, query: str):
        self.status_label.configure(text="⚡ Executing...", text_color="#10B981")
        self.card.configure(border_color="#10B981")
        self.input_field.delete(0, "end")
        self.input_field.insert(0, f"Running: {query}")

        threading.Thread(target=self._run_async_command, args=(query,), daemon=True).start()

    def _run_async_command(self, query: str):
        res = self.reasoning.process_command(query)
        msg = res.get("message", "Done!")

        self.after(0, lambda: self._show_result(msg))
        self._speak_text(msg)

    def _show_result(self, msg: str):
        self.status_label.configure(text="● Ready", text_color="#10B981")
        self.input_field.delete(0, "end")
        self.input_field.insert(0, msg)
        self.card.configure(border_color="#00E5FF")

    def _speak_text(self, text):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 185)
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass

    def _transcribe_audio(self, audio_data):
        try:
            transcript = self.recognizer.recognize_google(audio_data)
            self.after(0, lambda: self.execute_command(transcript))
        except Exception:
            self.after(0, lambda: self.status_label.configure(text="● Ready", text_color="#10B981"))
            self.after(0, lambda: self.card.configure(border_color="#00E5FF"))

    def audio_stream_worker(self):
        def audio_callback(indata, frames, time_info, status):
            volume_norm = float(np.linalg.norm(indata) * 10)
            self.audio_queue.put((indata.copy(), volume_norm))

        try:
            with sd.InputStream(callback=audio_callback, channels=1, samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE):
                while True:
                    try:
                        chunk, volume = self.audio_queue.get(timeout=0.2)
                        level = min(1.0, volume / 2.0)
                        self.after(0, lambda l=level: self.level_bar.set(l))

                        if self.is_recording:
                            self.audio_frames.append(chunk)

                    except queue.Empty:
                        continue
        except Exception as e:
            print(f"[AudioWorker] {e}")

    def setup_hotkeys(self):
        listener = keyboard.GlobalHotKeys({
            '<alt>+m': lambda: self.after(0, lambda: (self.input_field.focus(), self.lift(), self.attributes("-topmost", True))),
            '<alt>+s': lambda: self.after(0, lambda: self.execute_command("explain this slide"))
        })
        listener.daemon = True
        listener.start()

def main():
    print("[Mahesh Siri] Starting Hybrid Voice + Typing Dynamic Island...")
    app = MaheshSiriWidget()
    app.mainloop()

if __name__ == "__main__":
    main()
