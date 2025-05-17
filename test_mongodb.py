#!/usr/bin/env python3
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import certifi

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / "Mongo.env")

async def test_mongodb_connection():
    """Test MongoDB connection and check OTPs collection"""
    try:
        # Get MongoDB URI from environment
        mongodb_uri = os.getenv("MONGO_URI")
        if not mongodb_uri:
            print("ERROR: MongoDB URI is not set in environment variables")
            return

        print(f"Connecting to MongoDB...")
        
        # Connect to MongoDB with SSL certificate
        client = AsyncIOMotorClient(
            mongodb_uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
        )
        
        # Get database
        db = client.get_default_database()
        print(f"Connected to database: {db.name}")
        
        # List collections
        collections = await db.list_collection_names()
        print(f"Collections in database: {collections}")
        
        # Check if otps collection exists
        if "otps" not in collections:
            print("WARNING: 'otps' collection does not exist!")
        else:
            # Count documents in otps collection
            count = await db.otps.count_documents({})
            print(f"Number of documents in 'otps' collection: {count}")
            
            # Get a sample OTP to verify structure
            sample = await db.otps.find_one({})
            if sample:
                print("\nSample OTP document:")
                print(f"  ID: {sample['_id']}")
                print(f"  Email: {sample.get('email', 'N/A')}")
                print(f"  Code: {sample.get('code', 'N/A')}")
                print(f"  Created at: {sample.get('created_at', 'N/A')}")
                print(f"  Expires at: {sample.get('expires_at', 'N/A')}")
            else:
                print("No OTP documents found in collection")
        
        # Close connection
        client.close()
        
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection()) 