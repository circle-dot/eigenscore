from fastapi import FastAPI, Depends, HTTPException, Security, WebSocket, WebSocketDisconnect
from app.api.endpoints import rankings, quarkId
from app.utils.connection_manager import connection_manager
import os
from dotenv import load_dotenv
from fastapi.security.api_key import APIKeyHeader

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "access-token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI()

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

app.include_router(rankings.router, prefix="/rankings", tags=["score"], dependencies=[Depends(get_api_key)])
app.include_router(quarkId.router, prefix="/quarkid", tags=["quarkId"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Agora"}

@app.websocket("/ws/{invitation_id}")
async def websocket_endpoint(websocket: WebSocket, invitation_id: str):
    connection_manager.add_connection(invitation_id, websocket)
    await websocket.accept()
    print(f"WebSocket {invitation_id} connected")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data: {data}")
            # Handle incoming data if needed
    except WebSocketDisconnect:
        print(f"WebSocket {invitation_id} disconnected")
    finally:
        connection_manager.remove_connection(invitation_id)
