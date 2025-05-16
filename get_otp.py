import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path
import certifi
import sys

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / "Mongo.env")

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGO_URI")
if not MONGODB_URI:
    raise ValueError("MongoDB URI is not set in environment variables")

async def get_otp(email=None):
    client = AsyncIOMotorClient(
        MONGODB_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
    )
    db = client.get_default_database()
    
    # Use provided email or default
    target_email = email or "support@introgy.ai"
    
    # Get the most recent OTP for the email
    otp_cursor = db["otps"].find({"email": target_email}).sort("created_at", -1).limit(1)
    otp_list = await otp_cursor.to_list(length=1)
    
    if otp_list:
        otp = otp_list[0]
        print(f"Latest OTP for {target_email}: {otp['code']}")
        print(f"Created at: {otp['created_at']}")
        print(f"Expires at: {otp['expires_at']}")
    else:
        print(f"No OTP found for {target_email}")

    client.close()

if __name__ == "__main__":
    # Get email from command line argument if provided
    email = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(get_otp(email)) 