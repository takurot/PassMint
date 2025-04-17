from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from ..models.base import get_db
from ..models.models import User
from ..schemas.auth import LineAuthRequest, TokenResponse
from ..utils.line_auth import verify_line_id_token
from ..utils.auth import create_jwt_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/line", response_model=TokenResponse)
async def login_with_line(
    auth_request: LineAuthRequest, db: AsyncSession = Depends(get_db)
):
    """
    Verify LINE ID token and return JWT token
    """
    # Verify LINE ID token
    line_profile = await verify_line_id_token(auth_request.id_token)
    
    # Get LINE user ID
    line_user_id = line_profile.get("sub")
    if not line_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE ID token",
        )
    
    # Check if user exists in database
    stmt = select(User).where(User.line_user_id == line_user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    # If user doesn't exist, create new user
    if not user:
        user = User(
            id=uuid.uuid4(),
            line_user_id=line_user_id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # Create JWT token
    token = create_jwt_token(str(user.id), "user")
    
    # Return token response
    return TokenResponse(
        access_token=token,
        user_type="user",
        user_id=str(user.id),
    ) 