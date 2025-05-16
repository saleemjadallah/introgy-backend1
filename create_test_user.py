import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
import certifi

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / "Mongo.env")

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGO_URI")
if not MONGODB_URI:
    raise ValueError("MongoDB URI is not set in environment variables")

async def insert_test_user():
    client = AsyncIOMotorClient(
        MONGODB_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
    )
    db = client.get_default_database()
    
    # Check if user already exists
    existing_user = await db["users"].find_one({"email": "support@introgy.ai"})
    if existing_user:
        print("User already exists, no need to create again.")
        return
    
    # Create test user
    await db["users"].insert_one({
        "email": "support@introgy.ai",
        "hashed_password": "test_password",
        "display_name": "Support",
        "is_verified": False,
        "created_at": datetime.utcnow()
    })
    print("Test user created successfully.")

    client.close()

if __name__ == "__main__":
    asyncio.run(insert_test_user()) 