from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    project_id: UUID
    team_id: Optional[UUID] = None
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    assigned_to: Optional[UUID] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    priority: str = Field(default="MEDIUM")  # LOW, MEDIUM, HIGH, URGENT
    status: str = Field(default="TODO")      # TODO, IN_PROGRESS, REVIEW, COMPLETED

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    assigned_to: Optional[UUID] = None
    team_id: Optional[UUID] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class TaskStatusUpdate(BaseModel):
    status: str = Field(..., description="TODO, IN_PROGRESS, REVIEW, COMPLETED")

class TaskOut(BaseModel):
    id: UUID
    organization_id: UUID
    project_id: UUID
    project_name: Optional[str] = None
    team_id: Optional[UUID] = None
    team_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    assigned_to: Optional[UUID] = None
    assignee_name: Optional[str] = None
    created_by: Optional[UUID] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    status: str
    priority: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
