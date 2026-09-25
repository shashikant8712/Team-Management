from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.activity import ActivityLog

def log_activity(
    db: Session,
    organization_id: UUID,
    user_id: Optional[UUID],
    action: str,
    entity_type: str,
    entity_id: Optional[UUID],
    description: str
) -> ActivityLog:
    log_entry = ActivityLog(
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )
    db.add(log_entry)
    db.commit()
    return log_entry
