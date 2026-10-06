"""
Mahesh Desktop - Main Entrypoint
"""

import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.hud import MaheshDesktopHUD

def main():
    print("🚀 Starting Mahesh Desktop (Siri for Laptop)...")
    print("⌨️ Press [Alt + M] anywhere to toggle the floating HUD.")
    print("👀 Press [Alt + S] anywhere to analyze your screen silently.")

    app = MaheshDesktopHUD()
    app.mainloop()

if __name__ == "__main__":
    main()
