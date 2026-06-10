"""WebSocket endpoint for real-time hiring alerts."""
from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """In-memory connection manager (scale-out via Redis pub/sub in production)."""

    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        payload = json.dumps(message)
        dead: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws/hiring")
async def hiring_websocket(websocket: WebSocket) -> None:
    """Subscribe to real-time hiring events (interview, offer, risk alerts)."""
    await manager.connect(websocket)
    logger.info("websocket_connected", clients=len(manager.active))
    try:
        await websocket.send_json(
            {"type": "connected", "message": "Celestra Hiring AI real-time channel"}
        )
        while True:
            # Keep-alive: clients may send pings.
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("websocket_disconnected", clients=len(manager.active))
