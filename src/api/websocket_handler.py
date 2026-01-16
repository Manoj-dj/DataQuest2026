"""
WebSocket handler for real-time event streaming to frontend.
Broadcasts new disaster events as they arrive in the pipeline.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import asyncio
import json
from datetime import datetime
from src.utils.logger import app_logger

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = app_logger
    
    async def connect(self, websocket: WebSocket):
        """
        Accept new WebSocket connection.
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove disconnected WebSocket.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.logger.logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Send message to all connected clients.
        """
        if not self.active_connections:
            return
        
        message_json = json.dumps(message, default=str)
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                self.logger.log_error("WebSocket.broadcast", e)
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_personal(self, message: Dict[str, Any], websocket: WebSocket):
        """
        Send message to specific client.
        """
        try:
            message_json = json.dumps(message, default=str)
            await websocket.send_text(message_json)
        except Exception as e:
            self.logger.log_error("WebSocket.send_personal", e)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    """
    await manager.connect(websocket)
    
    try:
        await manager.send_personal({
            'type': 'connection',
            'message': 'Connected to DisasterLens AI real-time stream',
            'timestamp': datetime.now().isoformat()
        }, websocket)
        
        while True:
            data = await websocket.receive_text()
            
            if data == "ping":
                await manager.send_personal({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        app_logger.log_error("websocket_endpoint", e)
        manager.disconnect(websocket)

async def broadcast_new_event(event_data: Dict[str, Any]):
    """
    Helper function to broadcast new disaster events.
    """
    await manager.broadcast({
        'type': 'new_event',
        'event': event_data,
        'timestamp': datetime.now().isoformat()
    })
