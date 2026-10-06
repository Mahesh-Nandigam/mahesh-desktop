"""
⚡ MAHESH DESKTOP - HIGH-SPEED OS AUTOMATION ENGINE (PORT 5500)
"""

import os
import sys
import time
import subprocess
import webbrowser
import psutil
import pyautogui
from PIL import ImageGrab
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

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

app = FastAPI(title="Mahesh Siri Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

automations = DesktopAutomations()
reasoning = DesktopReasoningEngine(automations)

class CommandPayload(BaseModel):
    command: str

@app.post("/api/action")
def execute_action(payload: CommandPayload):
    cmd = payload.command.strip()
    result = reasoning.process_command(cmd)
    return JSONResponse(content=result)

@app.get("/api/status")
def get_system_metrics():
    return JSONResponse(content=automations.get_system_status())

@app.get("/", response_class=HTMLResponse)
def get_siri_island_page():
    with open(os.path.join(os.path.dirname(__file__), "ui", "siri_island.html"), "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5500, log_level="error")
