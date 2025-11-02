"""
Authentication utilities
Password hashing and JWT token management
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token
    
    Args:
        token: JWT token to decode
        
    Returns:
        Token payload data or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def get_initials(name: str) -> str:
    """
    Get initials from a name
    
    Args:
        name: Full name
        
    Returns:
        Initials (e.g., "John Doe" -> "JD")
    """
    parts = name.strip().split()
    if len(parts) == 0:
        return "?"
    elif len(parts) == 1:
        return parts[0][0].upper()
    else:
        return (parts[0][0] + parts[-1][0]).upper()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get the current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials from request
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    from database import get_database
    from models.user import User
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        
        if payload is None:
            raise credentials_exception
        
        user_id = payload.get("user_id")
        startup_id = payload.get("startup_id")
        
        if user_id is None or startup_id is None:
            raise credentials_exception
        
        # Fetch user from database
        db = get_database()
        user_data = await db.users.find_one({
            "_id": ObjectId(user_id),
            "startupId": startup_id
        })
        
        if user_data is None:
            raise credentials_exception
        
        # Convert ObjectId to string for Pydantic model
        if "_id" in user_data and isinstance(user_data["_id"], ObjectId):
            user_data["_id"] = str(user_data["_id"])
        
        return User(**user_data)
        
    except JWTError:
        raise credentials_exception


async def get_current_manager(current_user = Depends(get_current_user)):
    """
    Dependency to ensure current user is a manager
    
    Args:
        current_user: Current authenticated user from get_current_user
        
    Returns:
        User object if user is a manager
        
    Raises:
        HTTPException: If user is not a manager
    """
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can perform this action"
        )
    return current_user


async def get_current_teamlead(current_user = Depends(get_current_user)):
    """
    Dependency to ensure current user is a team lead
    
    Args:
        current_user: Current authenticated user from get_current_user
        
    Returns:
        User object if user is a team lead
        
    Raises:
        HTTPException: If user is not a team lead
    """
    if current_user.role != "teamlead":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leads can perform this action"
        )
    return current_user


async def get_current_user_ws(token: str):
    """
    WebSocket authentication - get current user from token
    
    Args:
        token: JWT token from WebSocket connection
        
    Returns:
        User object or None if invalid
    """
    from database import get_database
    from models.user import User
    
    try:
        payload = decode_access_token(token)
        
        if payload is None:
            return None
        
        user_id = payload.get("user_id")
        startup_id = payload.get("startup_id")
        
        if user_id is None or startup_id is None:
            return None
        
        # Fetch user from database
        db = get_database()
        user_data = await db.users.find_one({
            "_id": ObjectId(user_id),
            "startupId": startup_id
        })
        
        if user_data is None:
            return None
        
        # Convert ObjectId to string for Pydantic model
        if "_id" in user_data and isinstance(user_data["_id"], ObjectId):
            user_data["_id"] = str(user_data["_id"])
        
        return User(**user_data)
        
    except Exception:
        return None
