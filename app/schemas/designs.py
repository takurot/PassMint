from pydantic import BaseModel, Field, UUID4
from typing import Optional


class DesignCreate(BaseModel):
    template_json: dict = Field(..., description="JSON template for pass design")
    preview_url: Optional[str] = Field(None, description="URL to pass preview image")


class DesignResponse(BaseModel):
    id: UUID4
    org_id: UUID4
    template_json: dict
    preview_url: Optional[str] = None

    class Config:
        from_attributes = True 