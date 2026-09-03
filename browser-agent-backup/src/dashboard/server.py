import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Template
import uvicorn
from typing import Optional
from src.observability.manager import ObservabilityManager
from src.config import logger

app = FastAPI()
obs_manager: Optional[ObservabilityManager] = None

# Cyberpunk Dashboard HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Runtime Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0a0a0b;
            --accent-color: #00f2ff;
            --text-color: #e0e0e0;
            --panel-bg: rgba(20, 20, 25, 0.8);
            --border-color: #333;
            --success: #00ff9d;
            --warning: #ffcc00;
            --danger: #ff0055;
            --thinking: #bc00ff;
        }

        * { box-sizing: border-box; }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Fira Code', monospace;
            margin: 0;
            padding: 20px;
            overflow: hidden;
            height: 100vh;
        }

        .dashboard {
            display: grid;
            grid-template-columns: 350px 1fr 300px;
            grid-template-rows: auto 1fr 250px;
            gap: 15px;
            height: 100%;
        }

        .panel {
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 15px;
            position: relative;
            backdrop-filter: blur(10px);
            overflow: hidden;
        }

        .panel-header {
            font-size: 0.8rem;
            color: var(--accent-color);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
            display: flex;
            justify-content: space-between;
        }

        /* Header Bar */
        .header-bar {
            grid-column: 1 / -1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 20px;
            background: rgba(0, 242, 255, 0.05);
            border-bottom: 2px solid var(--accent-color);
        }

        .status-badge {
            padding: 4px 12px;
            border-radius: 2px;
            font-weight: bold;
            font-size: 0.9rem;
            animation: pulse 2s infinite;
        }

        .state-INITIALIZING { background: #555; }
        .state-THINKING { background: var(--thinking); color: white; }
        .state-NAVIGATING { background: #0066ff; color: white; }
        .state-EXTRACTING { background: #ffaa00; color: black; }
        .state-HUMAN_INTERVENTION { background: var(--danger); color: white; animation: blink 1s infinite; }
        .state-COMPLETED { background: var(--success); color: black; }
        .state-FAILED { background: var(--danger); color: white; }

        @keyframes blink {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        @keyframes pulse {
            0% { opacity: 0.8; }
            50% { opacity: 1; }
            100% { opacity: 0.8; }
        }

        /* Control Buttons */
        .controls {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 8px 16px;
            border: 1px solid var(--accent-color);
            background: transparent;
            color: var(--accent-color);
            font-family: inherit;
            cursor: pointer;
            text-transform: uppercase;
            font-size: 0.7rem;
            transition: all 0.2s;
        }

        .btn:hover {
            background: var(--accent-color);
            color: black;
        }

        .btn-danger {
            border-color: var(--danger);
            color: var(--danger);
        }

        .btn-danger:hover {
            background: var(--danger);
            color: white;
        }

        /* Graph/Timeline */
        .graph-panel {
            grid-column: 1 / 3;
            display: flex;
            flex-direction: column;
        }

        .graph-container {
            flex-grow: 1;
            display: flex;
            align-items: center;
            gap: 20px;
            overflow-x: auto;
            padding: 10px;
        }

        .graph-node {
            min-width: 120px;
            padding: 8px;
            border: 1px solid #444;
            background: rgba(255, 255, 255, 0.05);
            font-size: 0.6rem;
            position: relative;
            text-align: center;
        }

        .graph-node::after {
            content: "→";
            position: absolute;
            right: -15px;
            top: 50%;
            transform: translateY(-50%);
            color: #444;
        }

        .graph-node:last-child::after { display: none; }

        .node-action { border-color: var(--accent-color); }
        .node-error { border-color: var(--danger); }
        .node-goal { border-color: var(--success); }

        /* Thought/Action Area */
        .main-content {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .thought-box {
            font-style: italic;
            color: #aaa;
            line-height: 1.4;
            background: rgba(188, 0, 255, 0.05);
            padding: 15px;
            border-left: 3px solid var(--thinking);
            flex-grow: 1;
            overflow-y: auto;
        }

        .action-box {
            background: rgba(0, 242, 255, 0.05);
            padding: 15px;
            border-left: 3px solid var(--accent-color);
            font-size: 1.1rem;
        }

        /* Logs */
        .logs-panel {
            grid-column: 1 / 3;
            font-size: 0.75rem;
            display: flex;
            flex-direction: column;
        }

        .logs-container {
            flex-grow: 1;
            overflow-y: auto;
            color: #888;
        }

        .log-line {
            margin-bottom: 4px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.02);
            padding-bottom: 2px;
        }

        /* Screenshot Preview */
        .screenshot-panel {
            grid-row: 2 / 4;
            grid-column: 3;
        }

        .screenshot-preview {
            width: 100%;
            height: 100%;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
            border: 1px solid #222;
            object-fit: contain;
        }

        /* Glitch Effect for Title */
        .glitch {
            font-weight: bold;
            text-transform: uppercase;
            position: relative;
            text-shadow: 0.05em 0 0 rgba(255, 0, 0, 0.75),
                         -0.025em -0.05em 0 rgba(0, 255, 0, 0.75),
                         0.025em 0.05em 0 rgba(0, 0, 255, 0.75);
            animation: glitch 500ms infinite;
        }

        @keyframes glitch {
            0% { text-shadow: 0.05em 0 0 rgba(255, 0, 0, 0.75), -0.05em -0.025em 0 rgba(0, 255, 0, 0.75), -0.025em 0.05em 0 rgba(0, 0, 255, 0.75); }
            14% { text-shadow: 0.05em 0 0 rgba(255, 0, 0, 0.75), -0.05em -0.025em 0 rgba(0, 255, 0, 0.75), -0.025em 0.05em 0 rgba(0, 0, 255, 0.75); }
            15% { text-shadow: -0.05em -0.025em 0 rgba(255, 0, 0, 0.75), 0.025em 0.025em 0 rgba(0, 255, 0, 0.75), -0.05em -0.05em 0 rgba(0, 0, 255, 0.75); }
            49% { text-shadow: -0.05em -0.025em 0 rgba(255, 0, 0, 0.75), 0.025em 0.025em 0 rgba(0, 255, 0, 0.75), -0.05em -0.05em 0 rgba(0, 0, 255, 0.75); }
            50% { text-shadow: 0.025em 0.05em 0 rgba(255, 0, 0, 0.75), 0.05em 0 0 rgba(0, 255, 0, 0.75), 0 -0.05em 0 rgba(0, 0, 255, 0.75); }
            99% { text-shadow: 0.025em 0.05em 0 rgba(255, 0, 0, 0.75), 0.05em 0 0 rgba(0, 255, 0, 0.75), 0 -0.05em 0 rgba(0, 0, 255, 0.75); }
            100% { text-shadow: -0.025em 0 0 rgba(255, 0, 0, 0.75), -0.025em -0.025em 0 rgba(0, 255, 0, 0.75), -0.025em -0.05em 0 rgba(0, 0, 255, 0.75); }
        }

        .task-display {
            font-size: 0.9rem;
            color: var(--success);
            background: rgba(0, 255, 157, 0.05);
            padding: 10px;
            margin-bottom: 10px;
            border: 1px dashed var(--success);
        }
        
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent-color); }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header-bar">
            <div class="glitch">AGENT RUNTIME MONITOR</div>
            <div id="status-badge" class="status-badge state-INITIALIZING">INITIALIZING</div>
            <div style="font-size: 0.8rem; opacity: 0.7;">SESSION: <span id="session-id">---</span></div>
        </div>

        <!-- Left Sidebar: Metrics & Info -->
        <div class="panel">
            <div class="panel-header">RUNTIME METRICS</div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Runtime</div>
                    <div id="runtime" class="metric-value">00:00:00</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Steps</div>
                    <div id="step-count" class="metric-value">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Retries</div>
                    <div id="retry-count" class="metric-value">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Provider</div>
                    <div id="provider" class="metric-value" style="font-size: 0.8rem;">Ollama</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">VRAM Usage</div>
                    <div id="vram" class="metric-value">Local GPU</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Model</div>
                    <div id="model" class="metric-value" style="font-size: 0.7rem;">qwen2.5:7b</div>
                </div>
            </div>
            
            <div class="panel-header" style="margin-top: 20px;">CURRENT URL</div>
            <div id="current-url" style="font-size: 0.7rem; color: var(--accent-color); word-break: break-all;">None</div>
        </div>

        <!-- Center: Thinking & Action -->
        <div class="main-content">
            <div class="panel" style="flex-grow: 1; display: flex; flex-direction: column;">
                <div class="panel-header">AGENT EXECUTION</div>
                <div id="task-display" class="task-display">Initializing task...</div>
                
                <div class="panel-header" style="font-size: 0.6rem; opacity: 0.5;">THOUGHT PROCESS</div>
                <div id="thought-box" class="thought-box">Waiting for agent to start thinking...</div>
                
                <div class="panel-header" style="font-size: 0.6rem; opacity: 0.5; margin-top: 10px;">CURRENT ACTION</div>
                <div id="action-box" class="action-box">Standing by...</div>
                
                <div class="controls">
                    <button id="btn-takeover" class="btn btn-danger">Take Control</button>
                    <button id="btn-resume" class="btn" style="display:none;">Resume Agent</button>
                </div>
            </div>

            <div class="panel graph-panel">
                <div class="panel-header">DETERMINISTIC EXECUTION GRAPH</div>
                <div id="graph-container" class="graph-container">
                    <!-- Graph nodes will appear here -->
                </div>
            </div>
        </div>

        <!-- Right Sidebar: Screenshot -->
        <div class="panel screenshot-panel">
            <div class="panel-header">VISUAL FEED</div>
            <img id="screenshot" class="screenshot-preview" src="" alt="No visual feed">
        </div>

        <!-- Bottom: Logs -->
        <div class="panel logs-panel">
            <div class="panel-header">
                <span>SYSTEM LOGS</span>
                <span id="log-status">STREAMING</span>
            </div>
            <div id="logs-container" class="logs-container">
                <!-- Logs will be inserted here -->
            </div>
        </div>
    </div>

    <script>
        const statusBadge = document.getElementById('status-badge');
        const sessionIdEl = document.getElementById('session-id');
        const runtimeEl = document.getElementById('runtime');
        const stepCountEl = document.getElementById('step-count');
        const retryCountEl = document.getElementById('retry-count');
        const providerEl = document.getElementById('provider');
        const vramEl = document.getElementById('vram');
        const modelEl = document.getElementById('model');
        const currentUrlEl = document.getElementById('current-url');
        const taskDisplayEl = document.getElementById('task-display');
        const thoughtBoxEl = document.getElementById('thought-box');
        const actionBoxEl = document.getElementById('action-box');
        const logsContainer = document.getElementById('logs-container');
        const screenshotEl = document.getElementById('screenshot');
        const graphContainer = document.getElementById('graph-container');
        const btnTakeover = document.getElementById('btn-takeover');
        const btnResume = document.getElementById('btn-resume');

        btnTakeover.onclick = async () => {
            await fetch('/takeover', { method: 'POST' });
            btnTakeover.style.display = 'none';
            btnResume.style.display = 'inline-block';
        };

        btnResume.onclick = async () => {
            await fetch('/resume', { method: 'POST' });
            btnResume.style.display = 'none';
            btnTakeover.style.display = 'inline-block';
        };

        // Connect to Server-Sent Events
        const eventSource = new EventSource('/events');
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };

        function updateDashboard(data) {
            if (!data) return;

            // Update status
            statusBadge.innerText = data.current_state;
            statusBadge.className = 'status-badge state-' + data.current_state;
            
            // Update simple text fields
            runtimeEl.innerText = data.runtime || '00:00:00';
            stepCountEl.innerText = data.step_count || 0;
            retryCountEl.innerText = data.retry_count || 0;
            providerEl.innerText = 'Ollama';
            vramEl.innerText = 'GPU Active';
            modelEl.innerText = 'qwen2.5:7b';
            currentUrlEl.innerText = data.current_url || 'None';
            taskDisplayEl.innerText = data.current_task || 'No task assigned';
            
            // Update thought and action
            thoughtBoxEl.innerText = data.last_thought || 'Thinking...';
            actionBoxEl.innerText = data.last_action || 'Processing...';
            
            // Update Graph
            if (data.execution_graph && data.execution_graph.nodes) {
                const nodes = Object.values(data.execution_graph.nodes);
                graphContainer.innerHTML = nodes
                    .filter(n => n.id !== 'root')
                    .map(n => `<div class="graph-node node-${n.type}">${n.label}</div>`)
                    .join('');
            }
            
            // Update logs
            if (data.recent_logs) {
                logsContainer.innerHTML = data.recent_logs
                    .map(log => `<div class="log-line">${log}</div>`)
                    .join('');
            }

            // Update screenshot if available
            if (data.recent_screenshots && data.recent_screenshots.length > 0) {
                // Prepend /screenshot/ to the filename
                screenshotEl.src = '/screenshot/' + data.recent_screenshots[0];
            }
        }
        
        // Polling fallback for ID
        setInterval(async () => {
            try {
                const res = await fetch('/status');
                const data = await res.json();
                sessionIdEl.innerText = data.session_id || '---';
            } catch(e) {}
        }, 2000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return DASHBOARD_HTML

@app.post("/takeover")
async def takeover():
    if obs_manager:
        obs_manager.status.human_intervention_needed = True
        obs_manager.update_state(AgentState.HUMAN_INTERVENTION, last_action="User requested manual takeover.")
    return {"status": "Intervention requested"}

@app.post("/resume")
async def resume():
    if obs_manager:
        obs_manager.status.human_intervention_needed = False
        obs_manager.update_state(AgentState.THINKING, last_action="Human takeover concluded. Resuming...")
    return {"status": "Resuming agent"}

@app.get("/status")
async def get_status():
    if obs_manager:
        return {"session_id": obs_manager.session_id}
    return {"session_id": "Initializing..."}

@app.get("/events")
async def event_stream(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            
            if obs_manager:
                data = obs_manager.get_dashboard_data()
                # Correct SSE formatting: data: <payload>\n\n
                yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.5) # Update every 500ms
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/screenshot/{filename}")
async def get_screenshot(filename: str):
    from fastapi.responses import FileResponse
    return FileResponse(f"screenshots/{filename}")

def run_dashboard_server(manager: ObservabilityManager, port: int = 8000):
    global obs_manager
    obs_manager = manager
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    return server
