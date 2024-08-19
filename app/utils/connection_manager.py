from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.connections = {}

    def add_connection(self, invitation_id: str, websocket: WebSocket):
        self.connections[invitation_id] = websocket
        print(f"Connection added: {invitation_id}")

    def get_connection(self, invitation_id: str) -> WebSocket:
        websocket = self.connections.get(invitation_id)
        if websocket:
            print(f"Connection found for {invitation_id}")
        else:
            print(f"No connection found for {invitation_id}")
        return websocket

    def remove_connection(self, invitation_id: str):
        if invitation_id in self.connections:
            del self.connections[invitation_id]
            print(f"Connection removed: {invitation_id}")

# Singleton instance
connection_manager = ConnectionManager()
