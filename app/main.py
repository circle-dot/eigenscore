from fastapi import FastAPI, Depends, HTTPException, Security, Request, WebSocket, WebSocketDisconnect
from app.api.endpoints import rankings, quarkId
from app.utils.websocket_manager import ConnectionManager
import os
from dotenv import load_dotenv
from fastapi.security.api_key import APIKeyHeader

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "access-token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI()
manager = ConnectionManager()

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials")

app.include_router(rankings.router, prefix="/rankings", tags=["score"], dependencies=[Depends(get_api_key)])
app.include_router(quarkId.router, prefix="/quarkid", tags=["quarkId"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Agora"}

@app.websocket("/ws/{id}")
async def websocket_endpoint(websocket: WebSocket, id: str):
    await manager.connect(websocket, id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data from WebSocket {id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(id)
    except Exception as e:
        print(f"Error in WebSocket connection {id}: {str(e)}")
        manager.disconnect(id)
