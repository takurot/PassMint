from pydantic import BaseModel, UUID4
from typing import Dict, List
from datetime import datetime


class PassStats(BaseModel):
    total_issued: int
    active: int
    expired: int
    platforms: Dict[str, int]  # {"apple": 120, "google": 80}


class OrgStatsResponse(BaseModel):
    org_id: UUID4
    passes: PassStats
    recent_activity: List[Dict[str, datetime]]  # Recent pass creation timestamps
    updated_at: datetime 