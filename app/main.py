from fastapi import FastAPI
from app.api.endpoints import rankings

app = FastAPI()

# Include routers from the endpoints
app.include_router(rankings.router, prefix="/rankings", tags=["score"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Agora"}
