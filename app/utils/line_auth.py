import os
import jwt
import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")


async def verify_line_id_token(id_token: str) -> dict:
    """
    Verify LINE ID token and return user profile.
    
    In production, this should verify the signature of the JWT using the LINE Channel Secret.
    For simplicity, we're just decoding the token without verification.
    
    Args:
        id_token: LINE ID token from LIFF
        
    Returns:
        User profile data
    """
    try:
        # In production, should verify with LINE API
        # For now, just decode without verification
        decoded = jwt.decode(id_token, options={"verify_signature": False})
        
        # Expected fields in decoded token:
        # - sub: LINE user ID
        # - name: LINE user display name
        # - picture: LINE user profile image
        
        if not decoded.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid LINE ID token",
            )
        
        return decoded
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE ID token format",
        ) 