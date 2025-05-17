#!/usr/bin/env python
import asyncio
import json
import sys
from app.core.email import send_otp_email

async def test_otp_email():
    """Test sending an OTP email to the specified address."""
    if len(sys.argv) < 2:
        print("Usage: python test_otp.py <email_address>")
        return
    
    email = sys.argv[1]
    otp = "123456"  # Test OTP code
    
    print(f"Attempting to send OTP {otp} to {email}...")
    
    try:
        result = await send_otp_email(email, otp)
        print(f"SUCCESS! OTP email sent to {email}")
        print(f"Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"ERROR: Failed to send OTP email: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_otp_email())
