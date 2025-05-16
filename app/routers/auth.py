# Standard library imports
from datetime import datetime, timedelta
import random
from typing import Any, Dict, Optional
import os
import logging
import requests
import certifi

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

# Local imports
from app.core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    oauth2_scheme,
    verify_password,
)
from app.models.user import User, UserCreate, UserInDB

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

# Constants
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"

# Models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    email: Optional[str] = None

class VerificationRequest(BaseModel):
    email: EmailStr

class OTPVerification(BaseModel):
    email: EmailStr
    code: str

class PasswordReset(BaseModel):
    email: EmailStr
    new_password: str

def generate_otp(length: int = 6) -> str:
    """Generate a random OTP of specified length."""
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

async def send_email(to_email: str, subject: str, html_content: str) -> Dict[str, Any]:
    """Send an email using SendGrid API directly."""
    try:
        SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
        FROM_EMAIL = os.getenv('FROM_EMAIL', 'support@introgy.ai')
        FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Introgy Support')
        
        logger.info(f"Sending email to {to_email}")
        logger.info(f"Using FROM_EMAIL: {FROM_EMAIL}")
        logger.info(f"Using FROM_NAME: {FROM_NAME}")
        
        # Prepare SendGrid request
        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}]
                }
            ],
            "from": {
                "email": FROM_EMAIL,
                "name": FROM_NAME
            },
            "subject": subject,
            "content": [{
                "type": "text/html",
                "value": html_content
            }]
        }
        
        # Send request
        response = requests.post(
            SENDGRID_API_URL,
            headers=headers,
            json=data,
            verify=certifi.where(),
            timeout=30
        )
        
        # Log response
        logger.info(f"SendGrid Response Status: {response.status_code}")
        logger.info(f"SendGrid Response Headers: {dict(response.headers)}")
        logger.info(f"SendGrid Response Body: {response.text}")
        
        if response.status_code in [200, 201, 202]:
            return {"success": True, "message": "Email sent successfully"}
        else:
            error_msg = f"Failed to send email. Status: {response.status_code}, Body: {response.text}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
            
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

@router.post("/test-email")
async def test_email_endpoint(email: str) -> Dict[str, Any]:
    """Test endpoint to verify email delivery."""
    return await send_email(
        email,
        "Introgy Email Test",
        "<h1>Test Email</h1><p>This is a test email from Introgy backend.</p>"
    )

@router.post("/send-verification-code", response_model=Dict[str, Any])
async def send_verification_code(request: Request, verification: VerificationRequest) -> Dict[str, Any]:
    """Send verification code endpoint with enhanced logging."""
    logger.info(f"Starting verification code request for {verification.email}")
    
    try:
        # Check if user exists
        user = await request.app.mongodb["users"].find_one({"email": verification.email})
        logger.info(f"User exists check result: {user is not None}")
        
        # Generate and store OTP
        otp = generate_otp()
        logger.info(f"Generated new OTP for {verification.email}")
        
        # Store OTP in database
        try:
            await request.app.mongodb["otps"].insert_one({
                "email": verification.email,
                "code": otp,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=10)
            })
            logger.info("OTP stored in database successfully")
        except Exception as db_error:
            logger.error(f"Database error storing OTP: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(db_error)}"
            )
        
        # Send OTP via email
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50; text-align: center;">Verification Code</h2>
                    <p>Here is your verification code for Introgy:</p>
                    <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
                        <p style="font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #2c3e50;">
                            {otp}
                        </p>
                    </div>
                    <p style="margin-top: 20px;">This code will expire in 10 minutes.</p>
                    <p style="color: #7f8c8d; font-size: 12px;">
                        If you didn't request this code, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        await send_email(
            verification.email,
            "Your Introgy Verification Code",
            html_content
        )
        
        return {"success": True, "message": "Verification code sent"}
            
    except Exception as e:
        logger.error(f"Error in send_verification_code: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/send-otp", response_model=Dict[str, Any])
async def send_otp(request: Request, verification: VerificationRequest) -> Dict[str, Any]:
    return await send_verification_code(request, verification)

@router.post("/verify-otp", response_model=Dict[str, Any])
async def verify_otp(request: Request, verification: OTPVerification) -> Dict[str, Any]:
    # Find OTP in database
    otp_record = await request.app.mongodb["otps"].find_one({
        "email": verification.email,
        "code": verification.code,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )
    
    try:
        # Mark user as verified
        result = await request.app.mongodb["users"].update_one(
            {"email": verification.email},
            {"$set": {"is_verified": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Delete used OTP
        await request.app.mongodb["otps"].delete_one({"_id": otp_record["_id"]})
        
        return {"success": True, "message": "Email verified successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify OTP: {str(e)}"
        )

@router.post("/reset-password", response_model=Dict[str, Any])
async def reset_password(request: Request, reset_data: PasswordReset) -> Dict[str, Any]:
    try:
        # Update password
        result = await request.app.mongodb["users"].update_one(
            {"email": reset_data.email},
            {"$set": {"hashed_password": get_password_hash(reset_data.new_password)}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        return {"success": True, "message": "Password reset successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )

@router.post("/refresh-token", response_model=Token)
async def refresh_token(request: Request, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    # Create new access token
    access_token = create_access_token(data={"sub": current_user.email})
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 60 * 24  # 24 hours
    }

@router.get("/verify-token", response_model=Dict[str, Any])
async def verify_token(request: Request, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {"success": True, "user": current_user}

@router.get("/debug/otp-storage", response_model=Dict[str, Any])
async def debug_get_otp(request: Request, email: str):
    """Debug endpoint to retrieve OTP for a specific email (only in non-production)."""
    # Only allow in non-production environments
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug endpoints are not available in production"
        )
    
    try:
        # Get the most recent OTP for the email
        otp_cursor = request.app.mongodb["otps"].find({"email": email}).sort("created_at", -1).limit(1)
        otp_list = await otp_cursor.to_list(length=1)
        
        if not otp_list:
            return {"success": False, "message": f"No OTP found for {email}"}
        
        otp = otp_list[0]
        return {
            "success": True,
            "email": email,
            "code": otp["code"],
            "created_at": otp["created_at"].isoformat(),
            "expires_at": otp["expires_at"].isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve OTP: {str(e)}"
        )

@router.post("/debug/force-register", response_model=Dict[str, Any])
async def debug_force_register(request: Request, user: UserCreate):
    """Debug endpoint to force register and verify a user (only in non-production)."""
    # Only allow in non-production environments
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug endpoints are not available in production"
        )
    
    try:
        # Check if user already exists
        existing_user = await request.app.mongodb["users"].find_one({"email": user.email})
        if existing_user:
            # If user exists, update password and set verified
            result = await request.app.mongodb["users"].update_one(
                {"email": user.email},
                {"$set": {
                    "hashed_password": get_password_hash(user.password),
                    "display_name": user.display_name,
                    "is_verified": True
                }}
            )
            message = "User updated and verified"
        else:
            # Create new user document with verified status
            user_dict = {
                "email": user.email,
                "hashed_password": get_password_hash(user.password),
                "display_name": user.display_name,
                "is_verified": True,
                "created_at": datetime.utcnow(),
            }
            # Insert user into database
            await request.app.mongodb["users"].insert_one(user_dict)
            message = "User created and verified"
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        
        return {
            "success": True,
            "message": message,
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 60 * 24
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to force register user: {str(e)}"
        ) 