from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User, UserInDB
import os
from dotenv import load_dotenv
import secrets
import base64

# Load environment variables
load_dotenv()

# Security configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    # Generate a secure random key if not provided
    JWT_SECRET_KEY = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    print("Warning: JWT_SECRET_KEY not found in environment. Generated temporary key.")

JWT_ALGORITHM = "HS512"  # Using a stronger algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days

# Password hashing context with stronger settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased rounds for better security
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def generate_token_id():
    """Generate a unique token ID for JWT tracking."""
    return secrets.token_urlsafe(16)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token with enhanced security."""
    to_encode = data.copy()
    
    # Add token ID and issued at time for tracking
    to_encode.update({
        "jti": generate_token_id(),  # JWT ID for token tracking
        "iat": datetime.utcnow(),    # Issued at time
        "type": "access"             # Token type
    })
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Create token with stronger algorithm
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt

def create_refresh_token(user_id: str) -> str:
    """Create a refresh token with different expiration and claims."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": user_id,
        "type": "refresh",
        "jti": generate_token_id(),
        "iat": datetime.utcnow(),
        "exp": expire
    }
    
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

async def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify and decode a token with type checking."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        # Get user from database
        user = await request.app.mongodb["IntrogyUsers"].find_one({"email": email})
        
        if user is None:
            raise credentials_exception
        
        # Convert to User model
        return User(
            id=str(user["_id"]),
            email=user["email"],
            display_name=user.get("display_name"),
            is_verified=user.get("is_verified", False),
            created_at=user.get("created_at", datetime.utcnow())
        )
        
    except JWTError:
        raise credentials_exception 