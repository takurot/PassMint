import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_IN = 60 * 60 * 24 * 7  # 7 days


def create_jwt_token(user_id: str, user_type: str = "user") -> str:
    """
    Create a JWT token for the given user_id and user_type.
    
    Args:
        user_id: User or org ID
        user_type: Either "user" or "org"
        
    Returns:
        JWT token as string
    """
    payload = {
        "sub": user_id,
        "user_type": user_type,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRES_IN),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Dict:
    """
    Decode JWT token and return payload.
    
    Args:
        token: JWT token
        
    Returns:
        Token payload
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Tuple[str, str]:
    """
    Get current user from JWT token.
    
    Args:
        credentials: HTTP Bearer token
        
    Returns:
        Tuple of (user_id, user_type)
    """
    token = credentials.credentials
    payload = decode_jwt_token(token)
    user_id = payload.get("sub")
    user_type = payload.get("user_type", "user")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return user_id, user_type


async def get_current_org(
    current_user: Tuple[str, str] = Depends(get_current_user)
) -> str:
    """
    Get current org_id from JWT token. Verify it's an org token.
    
    Args:
        current_user: Tuple of (user_id, user_type) from get_current_user
        
    Returns:
        org_id
    """
    user_id, user_type = current_user
    if user_type != "org":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as organization",
        )
    return user_id 