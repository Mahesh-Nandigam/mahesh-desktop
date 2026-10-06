"""
⚡ MAHESH SIRI FOR WINDOWS
-------------------------------------------------------------------------
The Ultimate Apple-style Sovereign Voice & Screen AI Assistant for Windows.
- Runs 100% silently in the background with ZERO screen clutter.
- Continuous Wake Word listener: "Hey Mahesh", "Mahesh", "Hey Siri", "Hi Mahesh".
- Global Hotkeys: [Alt + M] to summon, [Alt + S] to analyze screen, [Escape] to dismiss.
- Real-time Floating Dynamic Island HUD with audio pulse visualizer.
- Instant OS Automations (Apps, Screen Vision, Auto-typing, Battery, Volume, Search).
- Voice response via pyttsx3 + Apple Siri Chime sound.
- System Tray resident icon.
-------------------------------------------------------------------------
"""

import os
import sys
import time
import queue
import threading
import winsound
import re
import datetime
import speech_recognition as sr
import pyttsx3
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray
from pynput import keyboard

# Ensure UTF-8 output encoding for Windows consoles
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

WAKE_WORDS = [
    "hey mahesh", "mahesh", "hey siri", "siri",
    "hi mahesh", "ok mahesh", "oye mahesh", "hello mahesh"
]

class MaheshSiriApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.automations = DesktopAutomations()
        self.reasoning = DesktopReasoningEngine(self.automations)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 280
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6
        self.recognizer.non_speaking_duration = 0.4

        # Window Styling (Apple Dynamic Island)
        self.title("Mahesh Siri")
        self.geometry("640x115")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#000000")

        self.is_visible = False
        self.is_busy = False
        self.voice_enabled = True
        self.auto_hide_timer = None

        self.position_island()
        self.setup_ui()
        
        # Hide window by default (Invisible background daemon until triggered)
        self.withdraw()

        # Initialize TTS in background worker
        self.tts_queue = queue.Queue()
        threading.Thread(target=self._tts_worker, daemon=True).start()

        # Setup System Tray & Global Hotkeys & Wake-word Listener
        self.setup_hotkeys()
        self.setup_system_tray()
        threading.Thread(target=self._background_wake_word_loop, daemon=True).start()

    def position_island(self):
        screen_w = self.winfo_screenwidth()
        x = (screen_w - 640) // 2
        y = 25 # 25px floating margin from top of monitor
        self.geometry(f"640x115+{x}+{y}")

    def setup_ui(self):
        # Outer Glowing Dynamic Island Pill
        self.card = ctk.CTkFrame(
            self,
            fg_color="#08090E",
            border_color="#00E5FF",
            border_width=2,
            corner_radius=26
        )
        self.card.pack(fill="both", expand=True, padx=2, pady=2)

        # Header Row
        self.header_row = ctk.CTkFrame(self.card, fg_color="transparent")
        self.header_row.pack(fill="x", padx=18, pady=(10, 2))

        # Brand / Orb Icon
        self.logo_label = ctk.CTkLabel(
            self.header_row,
            text="⚡ MAHESH SIRI",
            font=ctk.CTkFont(family="Plus Jakarta Sans", size=12, weight="bold"),
            text_color="#00E5FF"
        )
        self.logo_label.pack(side="left")

        # Audio Pulse Visualizer
        self.level_bar = ctk.CTkProgressBar(
            self.header_row,
            width=130,
            height=6,
            progress_color="#00E5FF",
            fg_color="#1E2230"
        )
        self.level_bar.set(0.0)
        self.level_bar.pack(side="left", padx=14)

        # Status indicator
        self.status_label = ctk.CTkLabel(
            self.header_row,
            text="● Listening...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#10B981"
        )
        self.status_label.pack(side="left")

        # Hotkey hints
        self.hint_label = ctk.CTkLabel(
            self.header_row,
            text="Alt+M: Summon | Alt+S: Screen Eye | Esc: Hide",
            font=ctk.CTkFont(size=10),
            text_color="#64748B"
        )
        self.hint_label.pack(side="right")

        # Action Input Row
        self.action_row = ctk.CTkFrame(self.card, fg_color="transparent")
        self.action_row.pack(fill="x", padx=16, pady=(4, 10))

        # Mic Action Orb
        self.mic_btn = ctk.CTkButton(
            self.action_row,
            text="🎙️",
            font=ctk.CTkFont(size=16),
            fg_color="#141824",
            hover_color="#00E5FF",
            text_color="#00E5FF",
            width=38,
            height=38,
            corner_radius=19,
            command=self.manual_mic_trigger
        )
        self.mic_btn.pack(side="left", padx=(0, 8))

        # Unified Input Bar
        self.input_field = ctk.CTkEntry(
            self.action_row,
            placeholder_text="Listening... or type ('battery', 'open vs code', 'explain slide')...",
            font=ctk.CTkFont(family="Plus Jakarta Sans", size=13),
            fg_color="#121520",
            border_color="#1F293D",
            border_width=1,
            text_color="#F8FAFC",
            height=38,
            corner_radius=12
        )
        self.input_field.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input_field.bind("<Return>", lambda e: self.on_text_submit())
        self.input_field.bind("<Escape>", lambda e: self.hide_island())

        # Run Button
        self.run_btn = ctk.CTkButton(
            self.action_row,
            text="Run",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#00E5FF",
            hover_color="#8B5CF6",
            text_color="#000",
            width=50,
            height=38,
            corner_radius=12,
            command=self.on_text_submit
        )
        self.run_btn.pack(side="right")

    def play_siri_chime(self):
        """Crisp Apple-style two-tone activation chime."""
        def _beep():
            try:
                winsound.Beep(587, 75)
                winsound.Beep(880, 110)
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()

    def show_island(self, initial_text: str = "", status: str = "● Listening...", color: str = "#00E5FF"):
        """Pops up the Dynamic Island at the top of the screen."""
        if self.auto_hide_timer:
            self.auto_hide_timer.cancel()

        self.is_visible = True
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.position_island()

        self.card.configure(border_color=color)
        self.status_label.configure(text=status, text_color=color)
        self.level_bar.set(0.6)
        
        if initial_text:
            self.input_field.delete(0, "end")
            self.input_field.insert(0, initial_text)
        
        self.input_field.focus()
        self.play_siri_chime()

    def hide_island(self):
        """Smoothly hides the island back into background mode."""
        self.is_visible = False
        self.input_field.delete(0, "end")
        self.level_bar.set(0.0)
        self.withdraw()

    def schedule_auto_hide(self, delay: float = 3.5):
        """Auto-hides the Dynamic Island after finishing."""
        if self.auto_hide_timer:
            self.auto_hide_timer.cancel()
        self.auto_hide_timer = threading.Timer(delay, lambda: self.after(0, self.hide_island))
        self.auto_hide_timer.start()

    def manual_mic_trigger(self):
        """Triggered via Mic Button or Alt+M."""
        self.show_island(status="● Listening to you...", color="#00E5FF")
        threading.Thread(target=self._capture_active_speech, daemon=True).start()

    def on_text_submit(self):
        query = self.input_field.get().strip()
        if not query:
            return
        self.execute_command(query)

    def execute_command(self, query: str):
        """Executes the voice or typed command through Reasoning Engine."""
        self.is_busy = True
        self.status_label.configure(text="⚡ Executing...", text_color="#8B5CF6")
        self.card.configure(border_color="#8B5CF6")
        self.level_bar.set(0.9)

        threading.Thread(target=self._async_execute_task, args=(query,), daemon=True).start()

    def _async_execute_task(self, query: str):
        # Clean wake word if present in query
        clean_query = query
        for w in WAKE_WORDS:
            clean_query = re.sub(rf'^{w}[,\s]*', '', clean_query, flags=re.IGNORECASE).strip()
        if not clean_query:
            clean_query = "status"

        res = self.reasoning.process_command(clean_query)
        msg = res.get("message", "Done!")

        self.after(0, lambda: self._update_ui_result(msg))
        self.speak(msg)
        self.is_busy = False
        self.schedule_auto_hide(4.0)

    def _update_ui_result(self, msg: str):
        self.status_label.configure(text="✅ Done", text_color="#10B981")
        self.card.configure(border_color="#10B981")
        self.input_field.delete(0, "end")
        self.input_field.insert(0, msg)
        self.level_bar.set(0.2)

    def speak(self, text: str):
        """Queues voice response without blocking UI."""
        # Strip emojis and markdown symbols for clean speech
        clean_speech = re.sub(r'[^\w\s.,!?-]', '', text).strip()
        if clean_speech:
            self.tts_queue.put(clean_speech)

    def _tts_worker(self):
        while True:
            text = self.tts_queue.get()
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 185)
                # Select a modern voice if available
                voices = engine.getProperty('voices')
                if len(voices) > 1:
                    engine.setProperty('voice', voices[1].id) # Often female / smooth voice on Windows
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"[TTS Error]: {e}")
            finally:
                self.tts_queue.task_done()

    def _capture_active_speech(self):
        """Records a single command when summoned."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = self.recognizer.listen(source, timeout=4.0, phrase_time_limit=6.0)
                transcript = self.recognizer.recognize_google(audio)
                self.after(0, lambda: self.input_field.delete(0, "end"))
                self.after(0, lambda: self.input_field.insert(0, transcript))
                self.after(0, lambda: self.execute_command(transcript))
        except sr.WaitTimeoutError:
            self.after(0, lambda: self.status_label.configure(text="● Timed out", text_color="#EF4444"))
            self.schedule_auto_hide(2.0)
        except sr.UnknownValueError:
            self.after(0, lambda: self.status_label.configure(text="● Couldn't hear clearly", text_color="#F59E0B"))
            self.schedule_auto_hide(2.0)
        except Exception as e:
            print(f"[Speech Error] {e}")
            self.schedule_auto_hide(1.5)

    def _background_wake_word_loop(self):
        """Continuous background listener that detects 'Hey Mahesh' or 'Hey Siri'."""
        print("[Mahesh Siri] 🎧 Background Wake Word listener started (Watching for 'Hey Mahesh')...")
        
        while True:
            if not self.voice_enabled or self.is_busy:
                time.sleep(0.5)
                continue

            try:
                with sr.Microphone() as source:
                    # Dynamic noise calibration
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                    
                    while self.voice_enabled and not self.is_busy:
                        try:
                            # Listen for phrase
                            audio = self.recognizer.listen(source, timeout=3.0, phrase_time_limit=6.0)
                            
                            try:
                                text = self.recognizer.recognize_google(audio).lower().strip()
                                print(f"[Heard in background]: '{text}'")

                                # Check for wake words
                                wake_detected = any(w in text for w in WAKE_WORDS)

                                if wake_detected:
                                    print(f"⚡ WAKE WORD ACTIVATED: '{text}'")
                                    
                                    # Extract any command spoken in the same breath
                                    command_part = text
                                    for w in WAKE_WORDS:
                                        command_part = re.sub(rf'^{w}[,\s]*', '', command_part, flags=re.IGNORECASE).strip()

                                    if command_part and len(command_part) > 2:
                                        # Immediate execution of combined command (e.g. "Hey Mahesh open vs code")
                                        self.after(0, lambda t=text: self.show_island(initial_text=t, status="⚡ Executing...", color="#8B5CF6"))
                                        self.after(0, lambda c=command_part: self.execute_command(c))
                                    else:
                                        # Standalone wake word ("Hey Mahesh") -> summon and listen for follow-up
                                        self.after(0, lambda: self.show_island(status="● Listening...", color="#00E5FF"))
                                        threading.Thread(target=self._capture_active_speech, daemon=True).start()

                                    time.sleep(1.0)

                            except sr.UnknownValueError:
                                pass # Normal ambient background sound
                            except sr.RequestError as e:
                                print(f"[Google STT Network Error]: {e}")
                                time.sleep(1.0)

                        except sr.WaitTimeoutError:
                            continue # Loop back smoothly

            except Exception as e:
                print(f"[Mic Loop Error]: {e}")
                time.sleep(2.0)

    def setup_hotkeys(self):
        """Global system-wide hotkeys that work from any Windows app."""
        def _on_summon():
            self.after(0, self.manual_mic_trigger)

        def _on_screen_vision():
            self.after(0, lambda: self.show_island(initial_text="Analyzing screen...", status="📸 Eye active...", color="#F59E0B"))
            self.after(0, lambda: self.execute_command("explain this slide"))

        def _on_escape():
            if self.is_visible:
                self.after(0, self.hide_island)

        try:
            hotkeys = keyboard.GlobalHotKeys({
                '<alt>+m': _on_summon,
                '<alt>+s': _on_screen_vision,
                '<esc>': _on_escape
            })
            hotkeys.daemon = True
            hotkeys.start()
            print("[Mahesh Siri] ⌨️ Global Hotkeys Registered: Alt+M (Summon), Alt+S (Screen Eye), Esc (Hide)")
        except Exception as e:
            print(f"[Hotkey Setup Error]: {e}")

    def setup_system_tray(self):
        """Creates a sleek Windows system tray icon."""
        def _create_image():
            # Generate a 64x64 neon cyber orb icon
            image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse((4, 4, 60, 60), fill="#0A0B10", outline="#00E5FF", width=4)
            draw.ellipse((20, 20, 44, 44), fill="#8B5CF6")
            return image

        def _on_show(icon, item):
            self.after(0, self.manual_mic_trigger)

        def _on_screen(icon, item):
            self.after(0, lambda: self.execute_command("explain this slide"))

        def _toggle_voice(icon, item):
            self.voice_enabled = not self.voice_enabled
            state = "Enabled" if self.voice_enabled else "Muted"
            print(f"[Mahesh Siri] Voice trigger {state}")

        def _on_exit(icon, item):
            icon.stop()
            self.after(0, self.destroy)
            os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("⚡ Summon Mahesh (Alt+M)", _on_show),
            pystray.MenuItem("📸 Analyze Screen (Alt+S)", _on_screen),
            pystray.MenuItem("🎙️ Toggle Voice Wake", _toggle_voice, checked=lambda item: self.voice_enabled),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit Mahesh", _on_exit)
        )

        self.tray_icon = pystray.Icon("Mahesh Siri", _create_image(), "Mahesh Siri (Listening in background)", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

def main():
    print("==================================================")
    print("⚡ MAHESH SIRI FOR WINDOWS - STARTING ENGINE")
    print("==================================================")
    print("● Status: Invisible Background Daemon Active")
    print("● Wake Word: Say 'Hey Mahesh' or 'Hey Siri'")
    print("● Global Hotkey: Press [Alt + M] to summon instantly")
    print("● Screen Eye: Press [Alt + S] to analyze screen/slide")
    print("● Dismiss: Press [Escape] or wait 3.5s to auto-hide")
    print("==================================================")

    app = MaheshSiriApp()
    app.mainloop()

if __name__ == "__main__":
    main()
