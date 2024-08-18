from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

@router.post("/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        if not data:  # Check if the request body is empty
            raise HTTPException(status_code=422, detail="Request body is empty")
        print('data', data)
        return {"message": "Data received successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing request: {str(e)}")