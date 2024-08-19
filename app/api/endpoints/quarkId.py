from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

@router.post("/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        if not isinstance(data, dict):  # Ensure data is a dictionary
            raise HTTPException(status_code=400, detail="Invalid data format")

        # Extract relevant data
        invitation_id = data.get('invitationId')
        verified = data.get('verified')
        raw_data = data.get('rawData')

        # Example debug print statements to check received data
        print('invitationId:', invitation_id)
        print('verified:', verified)
        print('rawData:', raw_data)

        # Notify the corresponding WebSocket client if connected
        if invitation_id in connected_clients:
            websocket = connected_clients[invitation_id]
            await websocket.send_json({"message": "Data received", "data": data})

        return {"message": "Data received successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing request: {str(e)}")
