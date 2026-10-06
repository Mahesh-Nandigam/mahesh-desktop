"""
Mahesh Desktop - Main Entrypoint
"""

import sys
import os

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.hud import MaheshDesktopHUD

def main():
    print("[Mahesh] Starting Mahesh Desktop (Siri for Laptop)...")
    print("[Mahesh] Shortcuts: [Alt + M] Toggle HUD | [Alt + S] Screen Eye")

    app = MaheshDesktopHUD()
    app.mainloop()

if __name__ == "__main__":
    main()
