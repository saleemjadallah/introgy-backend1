# Standard library imports
from datetime import datetime, timedelta
import random
from typing import Any, Dict, Optional
import os

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

# Local imports
from app.core.email import send_email, send_otp_email, send_verification_email
from app.core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    oauth2_scheme,
    verify_password,
)
from app.models.user import User, UserCreate, UserInDB

router = APIRouter(prefix="/auth", tags=["auth"])

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

@router.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, Any]:
    # Find user in database
    user = await request.app.mongodb["users"].find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["email"]})
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 60 * 24  # 24 hours
    }

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def register(request: Request, user: UserCreate) -> Dict[str, Any]:
    # Check if user already exists
    if await request.app.mongodb["users"].find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Hash password and create user document
    user_dict = {
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
        "display_name": user.display_name,
        "is_verified": False,
        "created_at": datetime.utcnow(),
    }
    
    try:
        # Insert user into database
        await request.app.mongodb["users"].insert_one(user_dict)
        
        # Send verification email
        await send_verification_email(user.email)
        
        return {
            "success": True,
            "message": "User registered successfully. Please check your email for verification."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )

@router.post("/send-verification-code", response_model=Dict[str, Any])
async def send_verification_code(request: Request, verification: VerificationRequest) -> Dict[str, Any]:
    # Check if user exists
    user = await request.app.mongodb["users"].find_one({"email": verification.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    try:
        # Generate and store OTP
        otp = generate_otp()
        await request.app.mongodb["otps"].insert_one({
            "email": verification.email,
            "code": otp,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        })
        
        # Send OTP via email
        await send_otp_email(verification.email, otp)
        
        return {"success": True, "message": "Verification code sent"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification code: {str(e)}"
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

@router.post("/test-email", response_model=Dict[str, Any])
async def test_email(email: EmailStr) -> Dict[str, Any]:
    """Test endpoint to verify email sending"""
    try:
        await send_email(
            to_email=email,
            subject="Introgy Email Test",
            html_content="""
            <html>
                <body>
                    <h1>Test Email</h1>
                    <p>This is a test email from Introgy to verify the email sending functionality.</p>
                </body>
            </html>
            """
        )
        return {"success": True, "message": "Test email sent successfully"}
    except Exception as e:
        print(f"Detailed error in test-email: {str(e)}")
        if hasattr(e, 'body'):
            print(f"Error body: {e.body}")
        if hasattr(e, 'headers'):
            print(f"Error headers: {e.headers}")
        return {
            "success": False, 
            "error": str(e),
            "error_type": type(e).__name__,
            "error_details": str(e.__dict__) if hasattr(e, '__dict__') else None
        }

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