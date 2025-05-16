from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging

import certifi
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.routes import router as main_router
from app.routers.auth import router as auth_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / "Mongo.env")
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")  # For other production settings

# Constants
VERSION = "1.0.0"

# Environment settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGO_URI")
if not MONGODB_URI:
    message = "MongoDB URI is not set in environment variables"
    if IS_PRODUCTION:
        logger.warning(f"{message}. Some functionality will be limited.")
        # In production, we'll still run the app but with limited functionality
        MONGODB_URI = "mongodb://localhost:27017/introgy"  # Fallback URI that won't connect
    else:
        raise ValueError(message)

app = FastAPI(
    title="Introgy API",
    description="Backend API for Introgy - The Introvert's Social Battery Manager",
    version=VERSION
)

# CORS configuration based on environment
allowed_origins = [
    "https://introgy.app",
]

# Add development origins if not in production
if not IS_PRODUCTION:
    allowed_origins.extend([
        "http://localhost:3000",
        "http://localhost:8000",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with distinct prefixes
app.include_router(main_router, prefix="/api/main")
app.include_router(auth_router, prefix="/api/auth")
# Add a second inclusion for the auth router to support both path formats
app.include_router(auth_router, prefix="/api/auth/auth")


@app.on_event("startup")
async def startup_db_client() -> None:
    """Initialize the MongoDB client during application startup."""
    try:
        app.mongodb_client = AsyncIOMotorClient(
            MONGODB_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,  # 5 second timeout for server selection
            connectTimeoutMS=10000,  # 10 second timeout for initial connection
        )
        app.mongodb = app.mongodb_client.get_default_database()
        
        # Verify database connection
        await app.mongodb_client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB - Environment: {ENVIRONMENT}")
    except (ConnectionFailure, ServerSelectionTimeoutError) as db_error:
        logger.error(f"Failed to connect to MongoDB: {db_error}")
        # In production, continue running even if MongoDB connection fails
        if not IS_PRODUCTION:
            raise
        else:
            logger.warning("Running in production with limited functionality (no database access)")
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        if not IS_PRODUCTION:
            raise


@app.on_event("shutdown")
async def shutdown_db_client() -> None:
    """Close the MongoDB client during application shutdown."""
    if hasattr(app, 'mongodb_client'):
        app.mongodb_client.close()


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint to verify API and database status."""
    status_info: Dict[str, Any] = {
        "status": "healthy",
        "version": VERSION,
        "environment": ENVIRONMENT,
        "mongodb_status": "disabled",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if hasattr(app, 'mongodb_client'):
        try:
            await app.mongodb_client.admin.command('ping')
            status_info["mongodb_status"] = "connected"
        except Exception as e:
            status_info["mongodb_status"] = "disconnected"
            logger.warning(f"Health check MongoDB ping failed: {str(e)}")
    
    return status_info


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint returning basic API information."""
    return {
        "message": "Welcome to the Introgy Backend!",
        "version": VERSION,
        "environment": ENVIRONMENT,
        "status": "running"
    } 