from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import datetime
import uuid

from ..models.base import get_db
from ..models.models import Pass
from ..schemas.stats import OrgStatsResponse, PassStats
from ..utils.auth import get_current_org

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/org/{org_id}", response_model=OrgStatsResponse)
async def get_org_stats(
    org_id: str,
    current_org: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Get organization stats
    """
    # Ensure the current org is requesting their own stats
    if current_org != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access stats for this organization",
        )
    
    # Query pass statistics
    stmt = select(
        func.count().label("total_issued"),
        func.sum(case(
            (Pass.expires_at > datetime.utcnow(), 1),
            else_=0
        )).label("active"),
        func.sum(case(
            (Pass.expires_at <= datetime.utcnow(), 1),
            else_=0
        )).label("expired")
    ).join(
        Pass.design
    ).filter(
        Pass.design.has(org_id=uuid.UUID(org_id))
    )
    
    result = await db.execute(stmt)
    stats_row = result.first()
    
    # Query platform distribution
    platform_stmt = select(
        Pass.platform,
        func.count().label("count")
    ).join(
        Pass.design
    ).filter(
        Pass.design.has(org_id=uuid.UUID(org_id))
    ).group_by(
        Pass.platform
    )
    
    platform_result = await db.execute(platform_stmt)
    platform_stats = {row.platform: row.count for row in platform_result}
    
    # Query recent activity (simplified version)
    activity_stmt = select(
        Pass.issued_at
    ).join(
        Pass.design
    ).filter(
        Pass.design.has(org_id=uuid.UUID(org_id))
    ).order_by(
        Pass.issued_at.desc()
    ).limit(10)
    
    activity_result = await db.execute(activity_stmt)
    recent_activity = [{"timestamp": row.issued_at} for row in activity_result]
    
    # Calculate total from active and expired in case of NULL values
    total_issued = stats_row.total_issued or 0
    active = stats_row.active or 0
    expired = stats_row.expired or 0
    
    # Build response
    return OrgStatsResponse(
        org_id=org_id,
        passes=PassStats(
            total_issued=total_issued,
            active=active,
            expired=expired,
            platforms=platform_stats
        ),
        recent_activity=recent_activity,
        updated_at=datetime.utcnow()
    ) 