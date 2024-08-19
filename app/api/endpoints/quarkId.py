from fastapi import APIRouter, HTTPException, Request
from app.utils.websocket_manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

@router.post("/")
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

        # Notify the corresponding WebSocket client if connected
        if invitation_id in manager.active_connections:
            websocket = manager.active_connections[invitation_id]
            await websocket.send_json({"message": "Data received", "data": data})

        return {"message": "Data received successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing request: {str(e)}")
