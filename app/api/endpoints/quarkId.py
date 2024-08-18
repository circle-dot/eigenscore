from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

@router.post("/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        return {"message": "Data received successfully", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing request: {str(e)}")
