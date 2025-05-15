from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from .routes import router
import certifi

# Load MongoDB credentials from Mongo.env in the backend folder
load_dotenv(dotenv_path=Path(__file__).parent.parent / "Mongo.env")

MONGODB_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/introgy")

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(
        MONGODB_URI,
        tlsCAFile=certifi.where()
    )
    app.mongodb = app.mongodb_client.get_default_database()

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

@app.get("/")
async def root():
    return {"message": "Welcome to the Introgy Backend!"} 