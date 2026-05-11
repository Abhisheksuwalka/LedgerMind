"""
WebSocket connection manager — extracted from main.py to declutter startup.
Tracks all active WebSocket connections and broadcasts JSON messages.
"""

import json
import logging
from fastapi.websockets import WebSocket

logger = logging.getLogger("ws.manager")


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.debug("[WS] Client connected — total=%d", len(self.active))

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        logger.debug("[WS] Client disconnected — total=%d", len(self.active))

    async def broadcast(self, message: dict):
        """Send JSON message to all connected clients. Dead connections are pruned."""
        dead = []
        payload = json.dumps(message)
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)
        if dead:
            logger.debug("[WS] Pruned %d dead connections", len(dead))
