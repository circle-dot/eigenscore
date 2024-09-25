from fastapi import FastAPI, Depends, HTTPException, Security, Request
from app.api.endpoints import rankings
import os
from dotenv import load_dotenv
from fastapi.security.api_key import APIKeyHeader
import json

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "access-token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to config.json
config_path = os.path.join(current_dir, 'config.json')

# Load configuration from JSON file
with open(config_path) as config_file:
    configs = json.load(config_file)

ALLOWED_ORIGINS = configs.get('allowed_origins', [])

app = FastAPI()

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

async def verify_origin(request: Request):
    origin = request.headers.get('origin')
    if origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="Origin not allowed")

app.include_router(rankings.router, prefix="/rankings", tags=["score"], dependencies=[Depends(get_api_key)])

@app.get("/")
def read_root():
    return {"message": "Welcome to Agora"}