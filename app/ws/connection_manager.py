from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Set


class ConnectionManager:
    def __init__(self):
        self.active_connections = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        if websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except RuntimeError:
                self.active_connections.discard(websocket)

    async def broadcast(self, message: str):
        disconnected_websockets = set()
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except RuntimeError:
                disconnected_websockets.add(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            self.active_connections.discard(websocket)


manager = ConnectionManager()

# class WebSocketManager:
#     def __init__(self):
#         self.active_connections: List[WebSocket] = []

#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)

#     def disconnect(self, websocket: WebSocket):
#         self.active_connections.remove(websocket)

#     async def send_personal_message(self, message: str, websocket: WebSocket):
#         await websocket.send_text(message)

#     async def broadcast(self, message: str):
#         for connection in self.active_connections:
#             await connection.send_text(message)
