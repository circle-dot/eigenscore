from fastapi import FastAPI, Depends, HTTPException, Security, Request
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

@app.get("/")
def read_root():
    return {"message": "Welcome to Agora"}

@app.post("/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        if not data:  # Check if the request body is empty
            raise HTTPException(status_code=422, detail="Request body is empty")
        print('data', data)
        return {"message": "Data received successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing request: {str(e)}")