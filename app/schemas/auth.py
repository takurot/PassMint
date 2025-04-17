from pydantic import BaseModel, Field


class LineAuthRequest(BaseModel):
    id_token: str = Field(..., description="LINE id_token from LIFF")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str  # "user" or "org"
    user_id: str


class ErrorResponse(BaseModel):
    error: dict = {"code": str, "message": str} 