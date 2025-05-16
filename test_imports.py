#!/usr/bin/env python3
"""
Test script to verify imports are working correctly.
Run this from the root project directory to test if auth.py and its dependencies can be imported.
"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Print environment info
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"PYTHONPATH: {sys.path}")
print(f"Environment: {os.getenv('ENVIRONMENT', 'Not set')}")
print("\nTesting imports...\n")

try:
    # Try to import auth module
    from app.routers import auth
    print("✓ Successfully imported app.routers.auth")
    
    # Try to import security module
    from app.core import security
    print("✓ Successfully imported app.core.security")
    
    # Try to import user models
    from app.models import user
    print("✓ Successfully imported app.models.user")
    
    # Try to import the auth dependencies
    from app.core.email import send_email
    print("✓ Successfully imported app.core.email")
    
    # Print some information about the imported modules
    print(f"\nAuth router prefix: {auth.router.prefix}")
    print(f"Auth router tags: {auth.router.tags}")
    print(f"Authentication scheme: {security.JWT_ALGORITHM}")
    
    print("\nAll imports are working correctly!")
    
except ImportError as e:
    print(f"✗ Import error: {str(e)}")
    print("\nTroubleshooting tips:")
    print("1. Make sure you're running this script from the project root directory")
    print("2. Check that all __init__.py files exist in the package directories")
    print("3. Verify PYTHONPATH includes the project root")
    print("4. Check for any typos in import statements")
    sys.exit(1)
    
except Exception as e:
    print(f"✗ Unexpected error: {str(e)}")
    sys.exit(1) 