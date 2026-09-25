from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    project_manager_id: Optional[UUID] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    priority: str = Field(default="MEDIUM")  # LOW, MEDIUM, HIGH
    status: str = Field(default="NOT_STARTED")

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    project_manager_id: Optional[UUID] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class ProjectMemberAdd(BaseModel):
    user_id: UUID

class ProjectMemberOut(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    assigned_at: datetime
    status: str

    class Config:
        from_attributes = True

class ProjectOut(BaseModel):
    id: UUID
    organization_id: UUID
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    team_id: Optional[UUID] = None
    team_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    project_manager_id: Optional[UUID] = None
    manager_name: Optional[str] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    priority: str
    status: str
    progress: int
    completion_date: Optional[datetime] = None
    archive_date: Optional[datetime] = None
    created_by: Optional[UUID] = None
    creator_name: Optional[str] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    members_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
