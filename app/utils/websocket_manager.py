from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, id: str):
        await websocket.accept()
        self.active_connections[id] = websocket
        print(f"WebSocket {id} connected")

    def disconnect(self, id: str):
        self.active_connections.pop(id, None)
        print(f"WebSocket {id} disconnected")

    async def send_message(self, id: str, message: str):
        if id in self.active_connections:
            await self.active_connections[id].send_text(message)
        else:
            print(f"WebSocket {id} not found")
