"""
Mahesh Desktop - Conversational Reasoning & Action Router
"""

import re
from core.automations import DesktopAutomations

class DesktopReasoningEngine:
    def __init__(self, automations: DesktopAutomations):
        self.automations = automations

    def process_command(self, query: str) -> dict:
        clean = query.strip()
        lower = clean.lower()

        # Strip prefixes
        lower_clean = re.sub(r'^(hey\s+mahesh|mahesh|please|can you|just)[,\s]*', '', lower).strip()

        # 1. SCREEN VISION / EXPLAIN SLIDE
        if any(w in lower_clean for w in ["screen", "slide", "look at", "explain this", "what is on", "solve this"]):
            screenshot_path = self.automations.capture_screen()
            return {
                "type": "screen_vision",
                "message": "📸 Screen captured! Analyzing lecture slide / content...",
                "screenshot_path": screenshot_path,
                "action": "explain_screen"
            }

        # 2. GHOST AUTO-TYPING
        if lower_clean.startswith("type") or lower_clean.startswith("write") or "draft an email" in lower_clean or "draft email" in lower_clean:
            # Generate email / text template
            if "professor" in lower_clean or "leave" in lower_clean or "attendance" in lower_clean or "assignment" in lower_clean:
                text_to_type = (
                    "Dear Professor,\n\n"
                    "I am writing to respectfully request your consideration regarding my attendance / assignment submission for today's class. "
                    "I was unwell and would greatly appreciate if you could kindly allow me to make up for the missed material.\n\n"
                    "Thank you for your understanding.\n\n"
                    "Sincerely,\nMahesh"
                )
            else:
                text_to_type = clean.replace("type", "").replace("write", "").strip()

            self.automations.ghost_type(text_to_type, delay_seconds=1.0)
            return {
                "type": "ghost_type",
                "message": "✍️ Auto-typed into your active window cursor!",
                "text": text_to_type
            }

        # 3. YOUTUBE SEARCH
        if "youtube" in lower_clean:
            search_terms = re.sub(r'.*(youtube|search youtube for|play on youtube)\s*', '', lower_clean).strip()
            if not search_terms or search_terms == "youtube":
                self.automations.open_url("youtube.com")
                return {"type": "app", "message": "Opening YouTube..."}
            else:
                self.automations.search_youtube(search_terms)
                return {"type": "search", "message": f"Searching YouTube for: '{search_terms}'"}

        # 4. GOOGLE / WEB SEARCH
        if lower_clean.startswith("search") or lower_clean.startswith("google"):
            search_terms = re.sub(r'^(search for|search|google for|google)\s*', '', lower_clean).strip()
            self.automations.search_google(search_terms)
            return {"type": "search", "message": f"Searching Google for: '{search_terms}'"}

        # 5. OPEN APP
        if lower_clean.startswith("open") or lower_clean.startswith("launch"):
            app_target = re.sub(r'^(open|launch)\s*', '', lower_clean).strip()
            msg = self.automations.open_app(app_target)
            return {"type": "app", "message": msg}

        # 6. VOLUME & SYSTEM CONTROLS
        if "mute" in lower_clean:
            msg = self.automations.control_volume("mute")
            return {"type": "system", "message": msg}
        if "volume up" in lower_clean:
            msg = self.automations.control_volume("up")
            return {"type": "system", "message": msg}
        if "volume down" in lower_clean:
            msg = self.automations.control_volume("down")
            return {"type": "system", "message": msg}

        # 7. BATTERY & PC STATS
        if "battery" in lower_clean or "status" in lower_clean or "pc stats" in lower_clean:
            stats = self.automations.get_system_status()
            charging_str = "⚡ Charging" if stats["is_charging"] else "🔋 On Battery"
            return {
                "type": "system",
                "message": f"Battery: {stats['battery_percent']}% ({charging_str}) | CPU: {stats['cpu_percent']} | RAM: {stats['ram_percent']}"
            }

        # DEFAULT CHIT-CHAT / ASSISTANCE
        return {
            "type": "chat",
            "message": f"I'm Mahesh! Press Alt+S to analyze your screen, or ask me to open an app, draft an email, or search."
        }
