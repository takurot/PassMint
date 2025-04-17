from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, Any
from datetime import datetime


class CreatePassRequest(BaseModel):
    design_id: UUID4 = Field(..., description="Design ID to create pass from")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for pass"
    )


class PlatformInfo(BaseModel):
    deep_link: str
    serial: Optional[str] = None


class Platforms(BaseModel):
    apple: Optional[PlatformInfo] = None
    google: Optional[PlatformInfo] = None


class CreatePassResponse(BaseModel):
    pass_id: UUID4
    platforms: Platforms
    qr_png: str
    expires_at: Optional[datetime] = None


class PassUpdateRequest(BaseModel):
    fields: Dict[str, Any] = Field(
        ..., description="Fields to update on the pass"
    ) 