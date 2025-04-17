from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import json
from typing import Optional

from ..models.base import get_db
from ..models.models import Design
from ..schemas.designs import DesignCreate, DesignResponse
from ..utils.auth import get_current_org
from ..utils.storage import storage

router = APIRouter(prefix="/designs", tags=["Designs"])


@router.post("", response_model=DesignResponse, status_code=status.HTTP_201_CREATED)
async def create_design(
    design: DesignCreate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new pass design
    """
    # Create new design
    new_design = Design(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        template_json=design.template_json,
        preview_url=design.preview_url,
    )
    
    # Save to database
    db.add(new_design)
    await db.commit()
    await db.refresh(new_design)
    
    # Return response
    return new_design


@router.post("/upload", response_model=DesignResponse, status_code=status.HTTP_201_CREATED)
async def upload_design(
    template_json: str = Form(...),
    preview_image: Optional[UploadFile] = File(None),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a pass design with file
    """
    # Parse template JSON
    try:
        template_data = json.loads(template_json)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format",
        )
    
    # Upload preview image if provided
    preview_url = None
    if preview_image:
        file_key = f"designs/{uuid.uuid4()}.{preview_image.filename.split('.')[-1]}"
        preview_url = await storage.upload_file(
            preview_image.file,
            file_key,
            content_type=preview_image.content_type,
        )
    
    # Create new design
    new_design = Design(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        template_json=template_data,
        preview_url=preview_url,
    )
    
    # Save to database
    db.add(new_design)
    await db.commit()
    await db.refresh(new_design)
    
    # Return response
    return new_design


@router.get("/{design_id}", response_model=DesignResponse)
async def get_design(
    design_id: str,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a pass design
    """
    # Get design from database
    stmt = select(Design).where(
        Design.id == uuid.UUID(design_id),
        Design.org_id == uuid.UUID(org_id)
    )
    result = await db.execute(stmt)
    design = result.scalars().first()
    
    # Check if design exists
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found",
        )
    
    # Return response
    return design 