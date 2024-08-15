from fastapi import FastAPI
from app.api.endpoints import getScores

app = FastAPI()

# Include routers from the endpoints
app.include_router(getScores.router, prefix="/rankings", tags=["score"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Agora"}
