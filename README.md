# Introgy Backend

This is the backend for the Introgy project, built with Python, FastAPI, and MongoDB.

## Stack
- **Python 3.10+**
- **FastAPI** (web framework)
- **Motor** (async MongoDB driver)
- **Uvicorn** (ASGI server)
- **Pydantic** (data validation)

## Features
- Async API endpoints
- MongoDB integration
- Environment-based configuration
- Ready for deployment on Amazon EC2

## Setup
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your MongoDB URI and secrets.
4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Deployment
- Deployable on Amazon EC2 (Ubuntu recommended)
- Use Nginx as a reverse proxy for HTTPS
- See FastAPI docs for production tips 