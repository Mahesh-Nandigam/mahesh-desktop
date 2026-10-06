"""
Mahesh Desktop - Windows OS System Automations
"""

import os
import subprocess
import webbrowser
import psutil
import pyautogui
from PIL import ImageGrab
import time

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

class DesktopAutomations:
    def __init__(self):
        self.screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def open_app(self, app_name: str) -> str:
        """Launches installed Windows applications or common tools."""
        clean = app_name.lower().strip()
        
        app_map = {
            "chrome": "start chrome",
            "google chrome": "start chrome",
            "brave": "start brave",
            "vs code": "code",
            "vscode": "code",
            "code": "code",
            "terminal": "start wt",
            "powershell": "start powershell",
            "cmd": "start cmd",
            "notepad": "notepad",
            "calculator": "calc",
            "calc": "calc",
            "spotify": "start spotify:",
            "settings": "start ms-settings:",
            "task manager": "taskmgr",
            "explorer": "explorer",
            "file explorer": "explorer",
            "whatsapp": "start whatsapp:"
        }

        cmd = app_map.get(clean)
        if cmd:
            subprocess.Popen(cmd, shell=True)
            return f"Opening {app_name}..."

        # Fallback to start command
        try:
            subprocess.Popen(f"start {app_name}", shell=True)
            return f"Launching {app_name}..."
        except Exception as e:
            return f"Couldn't launch {app_name}: {str(e)}"

    def open_url(self, url: str) -> str:
        """Opens URL or searches web."""
        if not url.startswith("http"):
            url = f"https://{url}"
        webbrowser.open(url)
        return f"Opening {url}"

    def search_google(self, query: str) -> str:
        """Searches query on Google."""
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return f"Searching Google for: '{query}'"

    def search_youtube(self, query: str) -> str:
        """Searches YouTube."""
        url = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)
        return f"Searching YouTube for: '{query}'"

    def capture_screen(self) -> str:
        """Captures a screenshot of the active desktop screen."""
        timestamp = int(time.time())
        file_path = os.path.join(self.screenshots_dir, f"screen_{timestamp}.png")
        screenshot = ImageGrab.grab()
        screenshot.save(file_path)
        return file_path

    def ghost_type(self, text: str, delay_seconds: float = 0.5) -> str:
        """Silently auto-types text into whatever active text cursor is focused."""
        time.sleep(delay_seconds)
        pyautogui.write(text, interval=0.01)
        return f"Typed {len(text)} characters into active window."

    def get_system_status(self) -> dict:
        """Returns battery, CPU, and RAM metrics."""
        battery = psutil.sensors_battery()
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram_usage = psutil.virtual_memory().percent

        return {
            "battery_percent": battery.percent if battery else "N/A (Desktop)",
            "is_charging": battery.power_plugged if battery else False,
            "cpu_percent": f"{cpu_usage}%",
            "ram_percent": f"{ram_usage}%"
        }

    def control_volume(self, action: str) -> str:
        """Mutes or changes volume using Windows media keys."""
        if action == "mute" or action == "toggle":
            pyautogui.press("volumemute")
            return "Toggled volume mute."
        elif action == "up":
            for _ in range(5): pyautogui.press("volumeup")
            return "Turned volume up."
        elif action == "down":
            for _ in range(5): pyautogui.press("volumedown")
            return "Turned volume down."
        return "Volume adjusted."
