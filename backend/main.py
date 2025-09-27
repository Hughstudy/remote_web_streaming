import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

    await browser_service.start()
    await vnc_service.start()

    yield

    # Shutdown
    await browser_service.stop()
    await vnc_service.stop()

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

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "running", "message": "AI Web Agent API is active"}

@app.post("/task")
async def create_task(task: dict):
    """Create a new AI task"""
    task_instruction = task.get("instruction", "")
    task_id = await ai_service.create_task(task_instruction)

    # Broadcast task creation to all connected clients
    await connection_manager.broadcast({
        "type": "task_created",
        "task_id": task_id,
        "instruction": task_instruction
    })

    return {"task_id": task_id, "status": "created"}

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
                vnc_info = vnc_service.get_connection_info()
                await connection_manager.send_personal_message({
                    "type": "vnc_info",
                    "data": vnc_info
                }, websocket)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True
    )