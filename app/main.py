from fastapi import FastAPI, Depends, HTTPException, Security, Request, WebSocket, WebSocketDisconnect
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from app.api.endpoints import rankings
from app.api.endpoints import quarkId
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "access-token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI()

# Dependency to check API key
async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

# Include routers with the API key dependency
app.include_router(rankings.router, prefix="/rankings", tags=["score"], dependencies=[Depends(get_api_key)])
app.include_router(quarkId.router, prefix="/quarkid", tags=["quarkId"])

# WebSocket Manager to handle connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, id: str):
        await websocket.accept()
        self.active_connections[id] = websocket

    def disconnect(self, id: str):
        self.active_connections.pop(id, None)

    async def send_message(self, id: str, message: str):
        if id in self.active_connections:
            await self.active_connections[id].send_text(message)

manager = ConnectionManager()

@app.get("/")
def read_root():
    return {"message": "Welcome to Agora"}

@app.post("/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        if not isinstance(data, dict):  # Ensure data is a dictionary
            raise HTTPException(status_code=400, detail="Invalid data format")

        invitation_id = data.get('invitationId')
        verified = data.get('verified')
        raw_data = data.get('rawData')

        # Example debug print statements to check received data
        print('invitationId:', invitation_id)
        print('verified:', verified)
        print('rawData:', raw_data)

        # Notify WebSocket client
        await manager.send_message(invitation_id, "Data received and processed")

        return {"message": "Data received successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing request: {str(e)}")

@app.websocket("/ws/{id}")
async def websocket_endpoint(websocket: WebSocket, id: str):
    await manager.connect(websocket, id)
    try:
        while True:
            # Keep the connection alive by receiving data
            data = await websocket.receive_text()
            print(f"Received data from WebSocket: {data}")
    except WebSocketDisconnect:
        manager.disconnect(id)
        print(f"WebSocket {id} disconnected")

