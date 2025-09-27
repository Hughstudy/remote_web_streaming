from typing import List
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected WebSockets"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)