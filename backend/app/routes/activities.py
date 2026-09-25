from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_membership, require_permission
from app.models.organization import OrganizationMember
from app.models.activity import ActivityLog
from app.models.user import User
from app.schemas.activity import ActivityOut

router = APIRouter(prefix="/activities", tags=["Activities"])

@router.get("/", response_model=List[ActivityOut])
def list_activities(
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = Query(None),
    membership: OrganizationMember = Depends(require_permission("activity.view")),
    db: Session = Depends(get_db)
):
    query = db.query(ActivityLog).filter(
        ActivityLog.organization_id == membership.organization_id
    )
    if action:
        query = query.filter(ActivityLog.action == action)

    activities = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()

    results = []
    for act in activities:
        u = db.query(User).filter(User.id == act.user_id).first() if act.user_id else None
        out = ActivityOut.model_validate(act)
        out.user_name = u.name if u else "System"
        results.append(out)

    return results
