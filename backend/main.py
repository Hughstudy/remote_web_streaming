import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from .services.browser_service import BrowserService
from .services.ai_service import AIService
from .services.vnc_service import VNCService
from .websocket_manager import ConnectionManager

load_dotenv()

# Global services
browser_service: BrowserService = None
ai_service: AIService = None
vnc_service: VNCService = None
connection_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global browser_service, ai_service, vnc_service

    # Startup
    browser_service = BrowserService()
    ai_service = AIService()
    vnc_service = VNCService()

    # Only start browser service - VNC is managed by supervisor in all-in-one mode
    await browser_service.start()
    # Don't start vnc_service - it's managed by supervisor

    yield

    # Shutdown
    await browser_service.stop()
    # Don't stop vnc_service - it's managed by supervisor

app = FastAPI(
    title="AI Web Agent - Remote Streaming",
    description="Autonomous AI agent with remote browser streaming",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "running", "message": "AI Web Agent API is active"}

@app.post("/task")
async def create_task(task: dict):
    """Create a new AI task"""
    try:
        task_instruction = task.get("instruction", "")
        task_id = await ai_service.create_task(task_instruction)

        # Broadcast task creation to all connected clients
        await connection_manager.broadcast({
            "type": "task_created",
            "task_id": task_id,
            "instruction": task_instruction
        })

        return {"task_id": task_id, "status": "created"}

    except ValueError as e:
        # Handle case where task cannot be created due to another running task
        return {"error": str(e), "status": "blocked"}

@app.get("/vnc_info")
async def get_vnc_info():
    """Get VNC connection information via HTTP"""
    # Use localhost for simplicity - works in Docker environment
    host = 'localhost'

    vnc_info = {
        "host": host,
        "port": 5901,  # Direct VNC port (not used directly, just for display)
        "display": ":1",
        "width": 1920,
        "height": 1080,
        "ws_url": f"ws://{host}:6901"  # WebSocket VNC port (websockify)
    }
    return {"type": "vnc_info", "data": vnc_info}

@app.post("/execute_task")
async def execute_task_http(task: dict):
    """Start task execution via HTTP and return task_id for WebSocket streaming"""
    try:
        task_id = task.get("task_id")
        if not task_id:
            return {"error": "task_id required", "status": "error"}

        # Broadcast start to WebSocket clients
        await connection_manager.broadcast({
            "type": "task_execution_started",
            "task_id": task_id
        })

        return {"task_id": task_id, "status": "execution_started", "message": "Connect to WebSocket for real-time updates"}

    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await connection_manager.connect(websocket)

    try:
        while True:
            # Listen for messages from client
            data = await websocket.receive_json()

            if data["type"] == "execute_task":
                task_id = data["task_id"]

                # Execute task with AI agent
                async for update in ai_service.execute_task(task_id):
                    await connection_manager.send_personal_message(update, websocket)

            elif data["type"] == "get_vnc_info":
                # Static VNC info for supervisor-managed VNC setup
                # Use the same host as the API request came from
                host = websocket.headers.get('host', 'localhost').split(':')[0]
                vnc_info = {
                    "host": host,
                    "port": 5901,  # Direct VNC port (not used directly, just for display)
                    "display": ":1",
                    "width": 1920,
                    "height": 1080,
                    "ws_url": f"ws://{host}:6901"  # WebSocket VNC port (websockify)
                }
                await connection_manager.send_personal_message({
                    "type": "vnc_info",
                    "data": vnc_info
                }, websocket)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
async def frontend():
    """Embedded frontend - no static files needed!"""
    return HTMLResponse(content="""<!DOCTYPE html>
<html>
<head>
    <title>AI Web Agent - Ultra Simple</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: monospace; margin: 20px; background: #1a1a1a; color: #00ff00; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #00ffff; text-align: center; margin-bottom: 20px; }
        .status { padding: 15px; margin: 10px 0; border-radius: 8px; font-weight: bold; }
        .status.connected { background: #0f4f0f; color: #00ff00; }
        .status.error { background: #4f0f0f; color: #ff6666; }
        .status.info { background: #0f0f4f; color: #6666ff; }
        .controls { margin: 20px 0; display: flex; gap: 10px; align-items: center; }
        input { flex: 1; padding: 12px; background: #333; border: 1px solid #555; color: #00ff00; font-family: inherit; }
        button { padding: 12px 20px; background: #0066cc; color: white; border: none; cursor: pointer; font-weight: bold; }
        .vnc-display { background: #000; min-height: 400px; border: 2px solid #333; margin: 20px 0; display: flex; align-items: center; justify-content: center; color: white; }
        .logs { background: #111; border: 1px solid #333; padding: 10px; height: 200px; overflow-y: auto; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AI Web Agent - Ultra Simple</h1>
        <div id="status" class="status info">Initializing...</div>

        <div class="controls">
            <input type="text" id="taskInput" placeholder="Enter AI task (e.g., search iPhone 17)" onkeydown="if(event.key==='Enter') submitTask()">
            <button onclick="submitTask()">🚀 Execute</button>
            <button onclick="getVNCInfo()">🖥️ Get VNC</button>
        </div>

        <div id="vnc-display" class="vnc-display">
            <div style="text-align: center;">
                <div style="font-size: 48px; margin-bottom: 20px;">🖥️</div>
                <div>Remote Browser Display</div>
                <div style="margin-top: 10px;">Click "Get VNC" to connect</div>
            </div>
        </div>

        <div id="logs" class="logs"></div>
    </div>

    <script>
        let ws = null;
        let vncInfo = null;

        function log(msg) {
            const logs = document.getElementById('logs');
            const time = new Date().toLocaleTimeString();
            logs.innerHTML += `[${time}] ${msg}\\n`;
            logs.scrollTop = logs.scrollHeight;
            console.log(msg);
        }

        function updateStatus(status, type = 'info') {
            const statusEl = document.getElementById('status');
            statusEl.textContent = status;
            statusEl.className = `status ${type}`;
            log(`STATUS: ${status}`);
        }

        async function getVNCInfo() {
            try {
                log('📡 Getting VNC info...');
                const response = await fetch('/vnc_info');
                const data = await response.json();

                if (data.type === 'vnc_info' && data.data) {
                    vncInfo = data.data;
                    log(`✅ VNC ready: ${vncInfo.ws_url}`);
                    updateStatus(`VNC Ready: ${vncInfo.ws_url}`, 'connected');

                    document.getElementById('vnc-display').innerHTML = `
                        <div style="text-align: center; color: white; padding: 20px;">
                            <div style="font-size: 24px; margin-bottom: 20px;">🖥️ VNC Info</div>
                            <div style="background: rgba(0,255,0,0.1); padding: 15px;">
                                <div><strong>WebSocket URL:</strong> ${vncInfo.ws_url}</div>
                                <div><strong>Resolution:</strong> ${vncInfo.width}x${vncInfo.height}</div>
                                <div><strong>Display:</strong> ${vncInfo.display}</div>
                            </div>
                            <div style="margin-top: 15px; color: #aaa;">
                                Connect VNC client to: localhost:5901
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                log(`❌ Failed to get VNC info: ${error.message}`);
                updateStatus('VNC Info Failed', 'error');
            }
        }

        function connectWebSocket() {
            if (ws && ws.readyState === WebSocket.OPEN) return;

            log('🔄 Connecting WebSocket...');
            const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${location.host}/ws`;
            ws = new WebSocket(wsUrl);
            log(`Connecting to: ${wsUrl}`);

            ws.onopen = () => {
                log('✅ WebSocket connected!');
                updateStatus('WebSocket Connected', 'connected');
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                log(`📥 ${data.type}: ${data.description || data.message || JSON.stringify(data)}`);

                if (data.type === 'step_update') {
                    updateStatus(`Step ${data.step_number}: ${data.description}`, 'info');
                } else if (data.type === 'task_complete') {
                    updateStatus('Task Completed!', 'connected');
                }
            };

            ws.onerror = () => {
                log('❌ WebSocket error');
                updateStatus('WebSocket Error', 'error');
            };

            ws.onclose = () => {
                log('🔌 WebSocket closed');
                updateStatus('WebSocket Disconnected', 'error');
            };
        }

        async function submitTask() {
            const input = document.getElementById('taskInput');
            const task = input.value.trim();
            if (!task) return;

            log(`🚀 Submitting task: ${task}`);

            try {
                // Create task
                const response = await fetch('/task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ instruction: task })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const taskData = await response.json();
                log(`✅ Task created: ${taskData.task_id}`);

                // Start execution
                const executeResponse = await fetch('/execute_task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_id: taskData.task_id })
                });

                if (executeResponse.ok) {
                    log(`🚀 Task execution started`);
                    updateStatus('Task Executing...', 'info');

                    // Connect WebSocket for updates
                    connectWebSocket();

                    // Send execute command via WebSocket
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: 'execute_task',
                            task_id: taskData.task_id
                        }));
                    }
                }

                input.value = '';

            } catch (error) {
                log(`❌ Task failed: ${error.message}`);
                updateStatus('Task Failed', 'error');
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            log('🚀 AI Web Agent initialized');
            updateStatus('Ready - Click "Get VNC" to connect', 'connected');
        });
    </script>
</body>
</html>""")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True
    )