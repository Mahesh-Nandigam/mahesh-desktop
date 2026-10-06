"""
Mahesh Desktop - Web Spotlight HUD Server
Runs locally and connects the web UI directly to real Windows automations!
"""

import os
import sys
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.automations import DesktopAutomations
from core.reasoning import DesktopReasoningEngine

app = FastAPI(title="Mahesh Desktop Web HUD")
automations = DesktopAutomations()
reasoning = DesktopReasoningEngine(automations)

class CommandRequest(BaseModel):
    command: str

@app.get("/", response_class=HTMLResponse)
def get_hud_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>⚡ mahesh- desktop spotlight</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #07070a;
                --surface: #0f1016;
                --card: #151722;
                --border: #23273a;
                --cyan: #00E5FF;
                --purple: #8B5CF6;
                --green: #10B981;
                --text: #F8FAFC;
                --text-muted: #94A3B8;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            body {
                background: var(--bg);
                color: var(--text);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 24px;
            }
            .hud-container {
                width: 100%;
                max-width: 680px;
                background: var(--surface);
                border: 2px solid var(--cyan);
                box-shadow: 0 0 50px rgba(0, 229, 255, 0.2), 0 20px 60px rgba(0,0,0,0.8);
                border-radius: 28px;
                padding: 28px;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            .header {
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .logo {
                font-size: 20px;
                font-weight: 800;
                background: linear-gradient(135deg, var(--cyan), var(--purple));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .badge {
                font-size: 11px;
                font-weight: 700;
                padding: 4px 12px;
                background: rgba(16, 185, 129, 0.15);
                border: 1px solid var(--green);
                color: var(--green);
                border-radius: 12px;
            }
            .input-wrapper {
                position: relative;
                display: flex;
                gap: 10px;
            }
            input {
                flex: 1;
                background: var(--card);
                border: 1px solid var(--border);
                color: #fff;
                font-size: 16px;
                padding: 16px 20px;
                border-radius: 16px;
                outline: none;
                transition: all 0.2s;
            }
            input:focus {
                border-color: var(--cyan);
                box-shadow: 0 0 15px rgba(0, 229, 255, 0.25);
            }
            button.send-btn {
                background: linear-gradient(135deg, var(--cyan), var(--purple));
                color: #000;
                border: none;
                font-weight: 800;
                font-size: 15px;
                padding: 0 28px;
                border-radius: 16px;
                cursor: pointer;
                transition: transform 0.15s;
            }
            button.send-btn:hover { transform: scale(1.03); }
            .chips-row {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            .chip {
                background: var(--card);
                border: 1px solid var(--border);
                color: var(--text-muted);
                padding: 8px 14px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }
            .chip:hover {
                border-color: var(--cyan);
                color: var(--cyan);
                background: rgba(0, 229, 255, 0.08);
            }
            .output-card {
                background: #090a0f;
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 18px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 13px;
                line-height: 1.6;
                color: #CBD5E1;
                min-height: 100px;
                max-height: 250px;
                overflow-y: auto;
            }
            .output-highlight { color: var(--green); font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="hud-container">
            <div class="header">
                <div class="logo">⚡ mahesh- desktop</div>
                <div class="badge">● Windows OS Connected</div>
            </div>

            <div class="input-wrapper">
                <input type="text" id="cmdInput" placeholder="Type a command: 'battery status', 'open vs code', 'draft email'..." autofocus onkeypress="if(event.key==='Enter') sendCommand()">
                <button class="send-btn" onclick="sendCommand()">Run</button>
            </div>

            <div class="chips-row">
                <div class="chip" onclick="setCmd('battery status')">🔋 Battery Stats</div>
                <div class="chip" onclick="setCmd('open vs code')">💻 Open VS Code</div>
                <div class="chip" onclick="setCmd('search youtube lofi study beats')">🎵 Lofi Music</div>
                <div class="chip" onclick="setCmd('explain this slide')">📸 Explain Screen</div>
                <div class="chip" onclick="setCmd('draft an email to professor')">✍️ Draft Email</div>
                <div class="chip" onclick="setCmd('mute volume')">🔇 Mute Volume</div>
            </div>

            <div class="output-card" id="outputCard">
                ⚡ Mahesh is standing by. Type a command or click a chip above to execute on your Windows PC!
            </div>
        </div>

        <script>
            function setCmd(cmd) {
                document.getElementById('cmdInput').value = cmd;
                sendCommand();
            }

            async function sendCommand() {
                const input = document.getElementById('cmdInput');
                const query = input.value.trim();
                if (!query) return;

                const out = document.getElementById('outputCard');
                out.innerHTML = `> User: ${query}<br>⏳ Executing on your PC...`;

                try {
                    const res = await fetch('/api/execute', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ command: query })
                    });
                    const data = await res.json();
                    out.innerHTML = `> User: ${query}<br><span class="output-highlight">⚡ Mahesh:</span> ${data.message}`;
                } catch (e) {
                    out.innerHTML = `<span style="color:#EF4444">❌ Error: Could not reach desktop service.</span>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/execute")
def execute_command(req: CommandRequest):
    result = reasoning.process_command(req.command)
    return JSONResponse(content=result)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
