from fastapi import APIRouter, HTTPException, Request, Depends
from app.utils.connection_manager import connection_manager

router = APIRouter()

@router.post("/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        print("Received data:", data)  # Log received data

        invitation_id = data.get('invitationId')
        if not invitation_id:
            raise HTTPException(status_code=400, detail="invitationId is required")

        websocket = connection_manager.get_connection(invitation_id)
        if not websocket:
            raise HTTPException(status_code=404, detail="WebSocket connection not found")

        await websocket.send_json({"message": "Data received", "data": data})
        return {"message": "Data received successfully"}
    except Exception as e:
        print("Error processing request:", str(e))  # Log error
        raise HTTPException(status_code=400, detail=f"Error processing request: {str(e)}")
