from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class ActivityOut(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: Optional[UUID] = None
    user_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    description: str
    created_at: datetime

    class Config:
        from_attributes = True
