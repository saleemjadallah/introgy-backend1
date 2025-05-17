import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Now import and run the app
from app.main import app
print(f"!!!! DIAGNOSTIC: app.main loaded from: {app.__file__} !!!!")
print(f"!!!! DIAGNOSTIC: app.docs_url is: {app.docs_url} !!!!")
print(f"!!!! DIAGNOSTIC: app.redoc_url is: {app.redoc_url} !!!!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",  # Changed from app object to string import
        host="0.0.0.0",
        port=8000,
        reload=True  # Temporarily enable reload for diagnostics
    ) 