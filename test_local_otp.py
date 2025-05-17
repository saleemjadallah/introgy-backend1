#!/usr/bin/env python3
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import uvicorn
import requests
import json

# Load local environment variables
load_dotenv(dotenv_path=Path(__file__).parent / "Local.env")

def test_otp_flow(email="test@example.com"):
    """Test the complete OTP flow locally"""
    base_url = "http://localhost:8000"
    
    print("\n=== Testing Local OTP Flow ===")
    print(f"Testing with email: {email}")
    
    try:
        # Step 1: Request OTP
        print("\n1. Requesting OTP...")
        response = requests.post(
            f"{base_url}/api/auth/send-verification-code",
            json={"email": email}
        )
        print(f"Response: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        if response.status_code != 200:
            print("❌ Failed to request OTP")
            return
        
        # Step 2: Get the OTP from the database (since we're in local development)
        print("\n2. Getting OTP from database...")
        from get_otp import get_otp
        asyncio.run(get_otp(email))
        
        # Step 3: Manual verification step
        print("\n3. Manual Verification:")
        print("✓ OTP request successful")
        print("✓ Check the console output above for the OTP code")
        print("\nNext steps:")
        print("1. Use the OTP code shown above to test verification")
        print("2. Make API calls to verify the OTP using your frontend or API client")
        print(f"   POST {base_url}/api/auth/verify-otp")
        print('   {"email": "' + email + '", "code": "OTPCODE"}')
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server. Is it running?")
    except Exception as e:
        print(f"❌ Error during OTP flow: {str(e)}")

if __name__ == "__main__":
    import sys
    
    # Start the local server if it's not running
    print("Ensuring local server is running...")
    try:
        requests.get("http://localhost:8000/docs")
    except requests.exceptions.ConnectionError:
        print("Starting local server...")
        # Start server in background
        import subprocess
        subprocess.Popen([sys.executable, "run.py"])
        import time
        time.sleep(2)  # Wait for server to start
    
    # Run the test
    test_email = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    test_otp_flow(test_email) 