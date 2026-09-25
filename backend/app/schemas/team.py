from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class TeamCreate(BaseModel):
    department_id: UUID
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    team_leader_id: Optional[UUID] = None

class TeamUpdate(BaseModel):
    department_id: Optional[UUID] = None
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    team_leader_id: Optional[UUID] = None
    status: Optional[str] = None

class TeamMemberAdd(BaseModel):
    user_id: UUID

class TeamMemberOut(BaseModel):
    id: UUID
    team_id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    user_role: Optional[str] = None
    joined_at: datetime
    status: str

    class Config:
        from_attributes = True

class TeamOut(BaseModel):
    id: UUID
    organization_id: UUID
    department_id: UUID
    department_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    team_leader_id: Optional[UUID] = None
    leader_name: Optional[str] = None
    status: str
    members_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
