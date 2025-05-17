from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging
import sys

import certifi
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.routes import router as main_router
from app.routers.auth import router as auth_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
env_files = [
    Path(__file__).parent.parent / "Mongo.env",
    Path(__file__).parent.parent / ".env"
]

for env_file in env_files:
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
        logger.info(f"Loaded environment from {env_file}")

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
        logger.error(f"{message}. Application cannot start without database connection.")
        raise ValueError(message)
    else:
        logger.warning(f"{message}. Using fallback local URI.")
        MONGODB_URI = "mongodb://localhost:27017/introgy"

app = FastAPI(
    title="Introgy API",
    description="Backend API for Introgy - The Introvert's Social Battery Manager",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
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

# Enhanced error handling middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.utcnow()
    try:
        response = await call_next(request)
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.info(
            f"Path: {request.url.path} | "
            f"Method: {request.method} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration:.3f}s"
        )
        return response
    except Exception as e:
        logger.error(
            f"Request failed: {request.url.path} | "
            f"Method: {request.method} | "
            f"Error: {str(e)}"
        )
        raise

# Database connection
@app.on_event("startup")
async def startup_db_client():
    try:
        app.mongodb_client = AsyncIOMotorClient(MONGODB_URI, tlsCAFile=certifi.where())
        app.mongodb = app.mongodb_client.get_default_database()
        await app.mongodb_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        if IS_PRODUCTION:
            raise HTTPException(status_code=500, detail="Database connection failed")

@app.on_event("shutdown")
async def shutdown_db_client():
    if hasattr(app, 'mongodb_client'):
        app.mongodb_client.close()
        logger.info("Closed MongoDB connection")

# Include routers with distinct prefixes
app.include_router(main_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")


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

@app.get("/test-diag-route")
async def test_diag_route():
    return {"message": "Diagnostic route is working!"} 