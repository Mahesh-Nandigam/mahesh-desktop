"""
Mahesh Desktop - Floating Glassmorphic Spotlight HUD
"""

import sys
import threading
import customtkinter as ctk
from pynput import keyboard
from core.automations import DesktopAutomations
from core.reasoning import DesktopReasoningEngine

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MaheshDesktopHUD(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.automations = DesktopAutomations()
        self.reasoning = DesktopReasoningEngine(self.automations)

        # Window styling
        self.title("Mahesh Desktop")
        self.geometry("640x360")
        self.resizable(False, False)
        
        # Frameless floating top-level
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#0A0A0E")

        # Center on screen
        self.center_window()

        self.is_visible = True
        self.setup_ui()
        self.setup_hotkeys()

    def center_window(self):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - 640) // 2
        y = (screen_h - 360) // 3
        self.geometry(f"640x360+{x}+{y}")

    def setup_ui(self):
        # Outer Border Frame
        self.border_frame = ctk.CTkFrame(
            self,
            fg_color="#0F1016",
            border_color="#00E5FF",
            border_width=2,
            corner_radius=20
        )
        self.border_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # Header Bar
        self.header_frame = ctk.CTkFrame(self.border_frame, fg_color="transparent", height=32)
        self.header_frame.pack(fill="x", padx=16, pady=(12, 4))

        self.logo_label = ctk.CTkLabel(
            self.header_frame,
            text="⚡ mahesh- desktop",
            font=ctk.CTkFont(family="Plus Jakarta Sans", size=14, weight="bold"),
            text_color="#00E5FF"
        )
        self.logo_label.pack(side="left")

        self.hint_label = ctk.CTkLabel(
            self.header_frame,
            text="Alt+M: Toggle | Alt+S: Screen Eye | ESC: Hide",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        )
        self.hint_label.pack(side="right")

        # Command Input
        self.input_entry = ctk.CTkEntry(
            self.border_frame,
            placeholder_text="Type command (e.g. 'explain slide', 'open vs code', 'mute volume')...",
            font=ctk.CTkFont(family="Plus Jakarta Sans", size=15),
            fg_color="#181A24",
            border_color="#2D3748",
            border_width=1,
            text_color="#F8FAFC",
            height=46,
            corner_radius=12
        )
        self.input_entry.pack(fill="x", padx=16, pady=8)
        self.input_entry.bind("<Return>", lambda e: self.on_submit())
        self.input_entry.bind("<Escape>", lambda e: self.hide_hud())
        self.input_entry.focus()

        # Quick Suggestion Chips
        self.chips_frame = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        self.chips_frame.pack(fill="x", padx=16, pady=4)

        chips = [
            ("📸 Explain Screen", "explain this slide"),
            ("💻 Open VS Code", "open vs code"),
            ("🎵 Lofi Study", "search youtube lofi study beats"),
            ("✍️ Draft Email", "draft an email to professor"),
            ("🔋 Battery", "battery status")
        ]

        for label, cmd in chips:
            btn = ctk.CTkButton(
                self.chips_frame,
                text=label,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#1E2230",
                hover_color="#7C3AED",
                text_color="#E2E8F0",
                height=26,
                corner_radius=8,
                command=lambda c=cmd: self.execute_command(c)
            )
            btn.pack(side="left", padx=3)

        # Output / Response Box
        self.output_box = ctk.CTkTextbox(
            self.border_frame,
            fg_color="#0A0B10",
            text_color="#CBD5E1",
            font=ctk.CTkFont(family="Consolas", size=13),
            border_color="#1E293B",
            border_width=1,
            corner_radius=12
        )
        self.output_box.pack(fill="both", expand=True, padx=16, pady=(8, 14))
        self.output_box.insert("0.0", "⚡ Mahesh Desktop Ready. Type a command or click a chip above.\n")

    def on_submit(self):
        query = self.input_entry.get().strip()
        if not query:
            return
        self.input_entry.delete(0, "end")
        self.execute_command(query)

    def execute_command(self, query: str):
        self.output_box.delete("0.0", "end")
        self.output_box.insert("end", f"> User: {query}\n")
        self.output_box.insert("end", "⏳ Processing...\n")
        self.update()

        threading.Thread(target=self._run_async_command, args=(query,), daemon=True).start()

    def _run_async_command(self, query: str):
        res = self.reasoning.process_command(query)
        msg = res.get("message", "Action completed.")
        
        self.after(0, lambda: self._update_output(msg))

    def _update_output(self, msg: str):
        self.output_box.delete("0.0", "end")
        self.output_box.insert("end", f"⚡ Mahesh: {msg}\n")

    def toggle_hud(self):
        if self.is_visible:
            self.hide_hud()
        else:
            self.show_hud()

    def show_hud(self):
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.input_entry.focus()
        self.is_visible = True

    def hide_hud(self):
        self.withdraw()
        self.is_visible = False

    def setup_hotkeys(self):
        def on_press(key):
            try:
                # Global Hotkey: Alt + M to toggle
                pass
            except Exception:
                pass

        # Global hotkey listener thread
        listener = keyboard.GlobalHotKeys({
            '<alt>+m': self.toggle_hud,
            '<alt>+s': lambda: self.execute_command("explain this slide")
        })
        listener.daemon = True
        listener.start()
