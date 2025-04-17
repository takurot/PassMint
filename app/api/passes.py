from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from typing import Dict, Any

from ..models.base import get_db
from ..models.models import Pass
from ..schemas.passes import CreatePassRequest, CreatePassResponse, PassUpdateRequest
from ..utils.auth import get_current_user, get_current_org
from ..services.issuer import issuer_service
from ..utils.qrcode import generate_qr_png_base64

router = APIRouter(prefix="/passes", tags=["Passes"])


@router.post("", response_model=CreatePassResponse, status_code=status.HTTP_201_CREATED)
async def create_pass(
    pass_request: CreatePassRequest,
    current_user: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new pass from a design template
    """
    user_id, user_type = current_user
    
    try:
        # Issue pass
        response = await issuer_service.issue_pass(
            db,
            user_id,
            str(pass_request.design_id),
            pass_request.metadata
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pass: {str(e)}",
        )


@router.get("/{pass_id}", response_model=Dict[str, Any])
async def get_pass(
    pass_id: str,
    current_user: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get pass details and QR code
    """
    user_id, user_type = current_user
    
    # Get pass from database
    stmt = select(Pass).where(
        Pass.id == uuid.UUID(pass_id),
        Pass.user_id == uuid.UUID(user_id)
    )
    result = await db.execute(stmt)
    passes = result.scalars().all()
    
    # Check if pass exists
    if not passes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pass not found",
        )
    
    # Organize by platform
    platforms = {}
    for p in passes:
        platforms[p.platform] = {
            "deep_link": p.deep_link,
            "serial": p.serial
        }
    
    # Generate QR code with the first available deep link
    first_pass = passes[0]
    qr_png = generate_qr_png_base64(first_pass.deep_link)
    
    # Return response
    return {
        "pass_id": str(first_pass.id),
        "platforms": platforms,
        "qr_png": qr_png,
        "expires_at": first_pass.expires_at
    }


@router.post("/{pass_id}/update")
async def update_pass(
    pass_id: str,
    update_request: PassUpdateRequest,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a pass
    """
    try:
        # Update pass
        success = await issuer_service.update_pass(
            db,
            pass_id,
            update_request.fields
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pass not found",
            )
        
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update pass: {str(e)}",
        ) 