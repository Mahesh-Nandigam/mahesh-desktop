"""
⚡ MAHESH DESKTOP - SIRI FOR WINDOWS ENTRYPOINT
"""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mahesh_siri import main

if __name__ == "__main__":
    main()
